package com.chrima.discord.controller;

import com.chrima.discord.api.IDiscordService;
import com.chrima.discord.api.dto.DiscordChannelResponse;
import com.chrima.discord.api.dto.DiscordGuildResponse;
import com.chrima.discord.api.dto.DiscordRoleResponse;
import com.chrima.discord.api.dto.DiscordUserResponse;
import com.chrima.discord.exception.DiscordChannelNotFoundException;
import com.chrima.discord.exception.DiscordRoleNotFoundException;
import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * Discord controller exposing Discord OAuth-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/discord/router.py}.
 */
@Slf4j
@RestController
@RequestMapping("/discord")
@RequiredArgsConstructor
public class DiscordController {

  private final IDiscordService discordService;
  private final IJwtService jwtService;

  @GetMapping("/me")
  public ResponseEntity<DiscordUserResponse> getDiscordMe(
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    return ResponseEntity.ok(discordService.getMe(payload.getSubject()));
  }

  @GetMapping("/guilds/{guildId}")
  public ResponseEntity<DiscordGuildResponse> getDiscordGuild(
      @PathVariable String guildId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    return ResponseEntity.ok(discordService.getGuild(payload.getSubject(), guildId));
  }

  @GetMapping("/guilds/{guildId}/channels/{channelId}")
  public ResponseEntity<DiscordChannelResponse> getDiscordGuildChannel(
      @PathVariable String guildId,
      @PathVariable String channelId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    List<DiscordChannelResponse> channels =
        discordService.getGuildChannels(payload.getSubject(), guildId);
    return channels.stream()
        .filter(c -> c.getId().equals(channelId))
        .findFirst()
        .map(ResponseEntity::ok)
        .orElseThrow(() -> new DiscordChannelNotFoundException(channelId));
  }

  @GetMapping("/guilds/{guildId}/channels")
  public ResponseEntity<List<DiscordChannelResponse>> getDiscordGuildChannels(
      @PathVariable String guildId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    return ResponseEntity.ok(discordService.getGuildChannels(payload.getSubject(), guildId));
  }

  @GetMapping("/guilds/{guildId}/roles/{roleId}")
  public ResponseEntity<DiscordRoleResponse> getDiscordGuildRole(
      @PathVariable String guildId,
      @PathVariable String roleId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    List<DiscordRoleResponse> roles = discordService.getGuildRoles(payload.getSubject(), guildId);
    return roles.stream()
        .filter(r -> r.getId().equals(roleId))
        .findFirst()
        .map(ResponseEntity::ok)
        .orElseThrow(() -> new DiscordRoleNotFoundException(roleId));
  }

  @GetMapping("/guilds/{guildId}/roles")
  public ResponseEntity<List<DiscordRoleResponse>> getDiscordGuildRoles(
      @PathVariable String guildId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    return ResponseEntity.ok(discordService.getGuildRoles(payload.getSubject(), guildId));
  }

  @GetMapping("/guilds")
  public ResponseEntity<List<DiscordGuildResponse>> getDiscordGuilds(
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    return ResponseEntity.ok(discordService.getGuilds(payload.getSubject()));
  }
}
