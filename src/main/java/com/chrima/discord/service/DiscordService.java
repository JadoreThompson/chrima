package com.chrima.discord.service;

import com.chrima.discord.api.IDiscordService;
import com.chrima.discord.api.dto.DiscordChannelResponse;
import com.chrima.discord.api.dto.DiscordGuildResponse;
import com.chrima.discord.api.dto.DiscordRoleResponse;
import com.chrima.discord.api.dto.DiscordUserResponse;
import com.chrima.discord.client.DiscordApiClient;
import com.chrima.discord.client.JsonUtil;
import com.chrima.discord.config.DiscordOAuthProperties;
import com.chrima.discord.encryption.EncryptionService;
import com.chrima.discord.exception.DiscordAccessTokenNotFoundException;
import com.chrima.discord.exception.DiscordGuildNotFoundException;
import com.chrima.discord.exception.DiscordUserNotFoundException;
import com.chrima.discord.exception.UserDiscordAccessTokenNotFoundException;
import com.chrima.discord.model.DiscordAccessToken;
import com.chrima.discord.model.UserDiscordAccessToken;
import com.chrima.discord.repository.DiscordAccessTokenRepository;
import com.chrima.discord.repository.UserDiscordAccessTokenRepository;
import com.fasterxml.jackson.databind.JsonNode;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Discord OAuth integration mirroring {@code chrima-backend/src/chrima/discord/service/discord.py}.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DiscordService implements IDiscordService {

  private final DiscordApiClient apiClient;
  private final DiscordOAuthProperties properties;
  private final EncryptionService encryptionService;
  private final DiscordAccessTokenRepository discordAccessTokenRepository;
  private final UserDiscordAccessTokenRepository userDiscordAccessTokenRepository;
  private final JsonUtil jsonUtil;

  @Value("${discord.token:}")
  private String botToken;

  @Override
  @Transactional
  public Map<String, Object> handleCallback(UUID userId, String code) {
    JsonNode data =
        apiClient.exchangeToken(
            Map.of(
                "client_id", properties.getClientId(),
                "client_secret", properties.getClientSecret(),
                "grant_type", "authorization_code",
                "code", code,
                "redirect_uri", properties.getRedirectUri()));

    JsonNode user = apiClient.getCurrentUser(data.get("access_token").asText());
    storeOauthPayload(user.get("id").asLong(), jsonUtil.toMap(data), userId);
    return jsonUtil.toMap(data);
  }

  @Override
  @Transactional
  public DiscordUserResponse handleSubscriberCallback(String code) {
    JsonNode data =
        apiClient.exchangeToken(
            Map.of(
                "client_id", properties.getClientId(),
                "client_secret", properties.getClientSecret(),
                "grant_type", "authorization_code",
                "code", code,
                "redirect_uri", properties.getSubscriberRedirectUri()));

    JsonNode user = apiClient.getCurrentUser(data.get("access_token").asText());
    storeOauthPayload(user.get("id").asLong(), jsonUtil.toMap(data), null);

    return DiscordUserResponse.builder()
        .id(user.get("id").asText())
        .username(user.get("username").asText())
        .avatar(user.hasNonNull("avatar") ? user.get("avatar").asText() : null)
        .build();
  }

  @Override
  @Transactional(readOnly = true)
  public DiscordUserResponse getMe(UUID userId) {
    UserDiscordAccessToken entity =
        userDiscordAccessTokenRepository
            .findById(userId)
            .orElseThrow(() -> new DiscordUserNotFoundException(userId));

    String accessToken = getAccessToken(userId, entity.getDiscordUserId());
    JsonNode user = apiClient.getCurrentUser(accessToken);
    return DiscordUserResponse.builder()
        .id(user.get("id").asText())
        .username(user.get("username").asText())
        .avatar(user.hasNonNull("avatar") ? user.get("avatar").asText() : null)
        .build();
  }

  @Override
  @Transactional(readOnly = true)
  public List<DiscordGuildResponse> getGuilds(UUID userId) {
    String accessToken = getAccessToken(userId, null);
    List<JsonNode> guilds = apiClient.getCurrentUserGuilds(accessToken);
    return guilds.stream()
        .filter(g -> g.hasNonNull("owner") && g.get("owner").asBoolean())
        .map(
            g ->
                DiscordGuildResponse.builder()
                    .id(g.get("id").asText())
                    .name(g.get("name").asText())
                    .avatar(g.hasNonNull("icon") ? g.get("icon").asText() : null)
                    .build())
        .toList();
  }

  @Override
  @Transactional(readOnly = true)
  public DiscordGuildResponse getGuild(UUID userId, String guildId) {
    return getGuilds(userId).stream()
        .filter(g -> g.getId().equals(guildId))
        .findFirst()
        .orElseThrow(() -> new DiscordGuildNotFoundException(guildId));
  }

  @Override
  @Transactional(readOnly = true)
  public List<DiscordChannelResponse> getGuildChannels(UUID userId, String guildId) {
    DiscordGuildResponse guild = getGuild(userId, guildId);
    List<JsonNode> channels = apiClient.getGuildChannels(botToken, guild.getId());
    return channels.stream()
        .filter(c -> c.hasNonNull("type") && c.get("type").asInt() == 0)
        .map(
            c ->
                DiscordChannelResponse.builder()
                    .id(c.get("id").asText())
                    .name(c.get("name").asText())
                    .build())
        .toList();
  }

  @Override
  @Transactional(readOnly = true)
  public List<DiscordRoleResponse> getGuildRoles(UUID userId, String guildId) {
    DiscordGuildResponse guild = getGuild(userId, guildId);
    List<JsonNode> roles = apiClient.getGuildRoles(botToken, guild.getId());
    return roles.stream()
        .map(
            r ->
                DiscordRoleResponse.builder()
                    .id(r.get("id").asText())
                    .name(r.get("name").asText())
                    .build())
        .toList();
  }

  /**
   * Resolves the OAuth access token for a Chrima user or Discord user, refreshing it if expired.
   *
   * @param userId Chrima user UUID (optional if discordUserId provided)
   * @param discordUserId Discord snowflake (optional if userId provided)
   * @return the raw Discord access token
   */
  @Transactional
  protected String getAccessToken(UUID userId, Long discordUserId) {
    TokenRow row;
    if (userId != null) {
      UserDiscordAccessToken entity =
          userDiscordAccessTokenRepository
              .findById(userId)
              .orElseThrow(() -> new UserDiscordAccessTokenNotFoundException(userId));
      row = new TokenRow(entity.getDiscordUserId(), entity.getPayload(), entity.getUpdatedAt());
    } else if (discordUserId != null) {
      DiscordAccessToken entity =
          discordAccessTokenRepository
              .findByUserId(discordUserId)
              .orElseThrow(() -> new DiscordAccessTokenNotFoundException(discordUserId));
      row = new TokenRow(discordUserId, entity.getPayload(), entity.getUpdatedAt());
    } else {
      throw new IllegalArgumentException("Either user_id or discord_user_id must be provided");
    }

    Map<String, Object> payload =
        encryptionService.decrypt(row.payload(), String.valueOf(row.discordUserId()));
    Object expiresInObj = payload.get("expires_in");
    if (expiresInObj instanceof Number expiresIn
        && row.updatedAt().getEpochSecond() + expiresIn.longValue()
            <= Instant.now().getEpochSecond()) {
      Object refreshToken = payload.get("refresh_token");
      Map<String, Object> refreshed = refreshAccessToken(String.valueOf(refreshToken));
      storeOauthPayload(row.discordUserId(), refreshed, userId);
      payload = refreshed;
    }
    return String.valueOf(payload.get("access_token"));
  }

  @Transactional
  protected Map<String, Object> refreshAccessToken(String refreshToken) {
    JsonNode data =
        apiClient.exchangeToken(
            Map.of(
                "client_id",
                properties.getClientId(),
                "client_secret",
                properties.getClientSecret(),
                "grant_type",
                "refresh_token",
                "refresh_token",
                refreshToken));
    return jsonUtil.toMap(data);
  }

  @Transactional
  protected void storeOauthPayload(long discordUserId, Map<String, Object> payload, UUID userId) {
    String encrypted = encryptionService.encrypt(payload, String.valueOf(discordUserId));
    if (userId != null) {
      UserDiscordAccessToken entity =
          userDiscordAccessTokenRepository.findById(userId).orElse(null);
      if (entity != null) {
        entity.setPayload(encrypted);
        entity.setDiscordUserId(discordUserId);
        userDiscordAccessTokenRepository.save(entity);
      } else {
        userDiscordAccessTokenRepository.save(
            UserDiscordAccessToken.builder()
                .userId(userId)
                .discordUserId(discordUserId)
                .payload(encrypted)
                .build());
      }
      return;
    }
    DiscordAccessToken tokenEntity =
        discordAccessTokenRepository.findByUserId(discordUserId).orElse(null);
    if (tokenEntity != null) {
      tokenEntity.setPayload(encrypted);
      discordAccessTokenRepository.save(tokenEntity);
    } else {
      discordAccessTokenRepository.save(
          DiscordAccessToken.builder().userId(discordUserId).payload(encrypted).build());
    }
  }

  private record TokenRow(long discordUserId, String payload, Instant updatedAt) {}
}
