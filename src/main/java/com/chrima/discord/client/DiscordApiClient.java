package com.chrima.discord.client;

import com.chrima.discord.config.DiscordOAuthProperties;
import com.chrima.discord.exception.DiscordApiException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * Thin HTTP client for the Discord REST API mirroring the aiohttp calls in {@code
 * chrima-backend/src/chrima/discord/service/discord.py}.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DiscordApiClient {

  private final DiscordOAuthProperties properties;
  private final ObjectMapper objectMapper;
  private final HttpClient httpClient =
      HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();

  /** POST /oauth2/token with a form-encoded body. */
  public JsonNode exchangeToken(Map<String, String> body) {
    String form =
        body.entrySet().stream()
            .map(
                e ->
                    URLEncoder.encode(e.getKey(), StandardCharsets.UTF_8)
                        + "="
                        + URLEncoder.encode(e.getValue(), StandardCharsets.UTF_8))
            .collect(Collectors.joining("&"));
    HttpRequest request =
        HttpRequest.newBuilder(URI.create(properties.getApiBaseUrl() + "/oauth2/token"))
            .header("Content-Type", "application/x-www-form-urlencoded")
            .POST(HttpRequest.BodyPublishers.ofString(form))
            .timeout(Duration.ofSeconds(15))
            .build();
    return send(request);
  }

  public JsonNode getCurrentUser(String accessToken) {
    HttpRequest request =
        HttpRequest.newBuilder(URI.create(properties.getApiBaseUrl() + "/users/@me"))
            .header("Authorization", "Bearer " + accessToken)
            .GET()
            .timeout(Duration.ofSeconds(15))
            .build();
    return send(request);
  }

  public List<JsonNode> getCurrentUserGuilds(String accessToken) {
    JsonNode body =
        send(
            HttpRequest.newBuilder(URI.create(properties.getApiBaseUrl() + "/users/@me/guilds"))
                .header("Authorization", "Bearer " + accessToken)
                .GET()
                .timeout(Duration.ofSeconds(15))
                .build());
    return asList(body);
  }

  public List<JsonNode> getGuildChannels(String botToken, String guildId) {
    JsonNode body =
        send(
            HttpRequest.newBuilder(
                    URI.create(properties.getApiBaseUrl() + "/guilds/" + guildId + "/channels"))
                .header("Authorization", "Bot " + botToken)
                .GET()
                .timeout(Duration.ofSeconds(15))
                .build());
    return asList(body);
  }

  public List<JsonNode> getGuildRoles(String botToken, String guildId) {
    JsonNode body =
        send(
            HttpRequest.newBuilder(
                    URI.create(properties.getApiBaseUrl() + "/guilds/" + guildId + "/roles"))
                .header("Authorization", "Bot " + botToken)
                .GET()
                .timeout(Duration.ofSeconds(15))
                .build());
    return asList(body);
  }

  private JsonNode send(HttpRequest request) {
    try {
      HttpResponse<String> response =
          httpClient.send(request, HttpResponse.BodyHandlers.ofString());
      if (response.statusCode() != 200) {
        log.error(
            "Discord API error status={} uri={} body={}",
            response.statusCode(),
            request.uri(),
            response.body());
        throw new DiscordApiException(
            String.format("Discord API request failed (%d)", response.statusCode()));
      }
      return objectMapper.readTree(response.body());
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new DiscordApiException("Discord API request interrupted");
    } catch (DiscordApiException e) {
      throw e;
    } catch (Exception e) {
      log.error("Discord API request failed uri={}", request.uri(), e);
      throw new DiscordApiException("Discord API request failed");
    }
  }

  private List<JsonNode> asList(JsonNode body) {
    return objectMapper.convertValue(body, new TypeReference<List<JsonNode>>() {});
  }
}
