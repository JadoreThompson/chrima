package com.chrima.notification.discord.service;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.api.IDiscordNotificationService;
import com.chrima.notification.discord.model.DiscordNotification;
import com.chrima.notification.discord.repository.DiscordNotificationRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class DiscordNotificationService implements IDiscordNotificationService {

  private final DiscordNotificationRepository discordNotificationRepository;
  private final ObjectMapper objectMapper;

  @Override
  @Transactional
  public void publish(
      Long guildId,
      Long channelId,
      String type,
      IDiscordNotificationContent content,
      String idempotencyKey) {
    if (guildId == null) {
      throw new IllegalArgumentException("guildId cannot be null");
    }

    if (channelId == null) {
      throw new IllegalArgumentException("channelId cannot be null");
    }

    if (type == null || type.isBlank()) {
      throw new IllegalArgumentException("type must not be blank");
    }

    if (idempotencyKey == null || idempotencyKey.isBlank()) {
      throw new IllegalArgumentException("idempotencyKey must not be blank");
    }

    if (discordNotificationRepository.existsByIdempotencyKey(idempotencyKey)) {
      return;
    }

    discordNotificationRepository.save(
        DiscordNotification.builder()
            .guildId(guildId)
            .channelId(channelId)
            .type(type)
            .content(serialize(content))
            .idempotencyKey(idempotencyKey)
            .build());
  }

  private String serialize(IDiscordNotificationContent content) {
    try {
      return objectMapper.writeValueAsString(content);
    } catch (JsonProcessingException e) {
      throw new IllegalArgumentException("Failed to serialize Discord notification content", e);
    }
  }
}
