package com.chrima.notification.discord.service;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.channel.DiscordNotificationChannel;
import com.chrima.notification.discord.config.DiscordPollingProperties;
import com.chrima.notification.discord.model.DiscordNotification;
import com.chrima.notification.discord.model.DiscordNotificationContentRegistry;
import com.chrima.notification.discord.model.enums.DiscordNotificationStatus;
import com.chrima.notification.discord.repository.DiscordNotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Instant;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.data.domain.PageRequest;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
@ConditionalOnProperty(name = "discord.token")
@ConditionalOnProperty(
    name = "discord.polling.enabled",
    havingValue = "true",
    matchIfMissing = true)
public class DiscordNotificationPoller {

  private final DiscordNotificationRepository discordNotificationRepository;
  private final DiscordNotificationChannel discordNotificationChannel;
  private final DiscordPollingProperties properties;
  private final ObjectMapper objectMapper;
  private final DiscordNotificationContentRegistry registry;

  @Scheduled(
      fixedDelayString = "${discord.polling.fixed-delay}",
      initialDelayString = "${discord.polling.initial-delay}")
  @Transactional
  public void run() {
    List<DiscordNotification> pending =
        discordNotificationRepository.findPending(PageRequest.of(0, properties.getBatchSize()));
    for (DiscordNotification notification : pending) {
      try {
        IDiscordNotificationContent content =
            objectMapper.readValue(notification.getContent(), registry.get(notification.getType()));
        Long discordMessageId =
            discordNotificationChannel.send(
                notification.getGuildId(),
                notification.getChannelId(),
                content,
                notification.getIdempotencyKey());
        int updatedAttempts =
            (notification.getAttempts() == null ? 0 : notification.getAttempts()) + 1;
        notification.setAttempts(updatedAttempts);
        notification.setLastAttemptedAt(Instant.now());
        notification.markDispatched(discordMessageId);
        notification.setStatus(DiscordNotificationStatus.COMPLETED);
      } catch (Exception e) {
        int updatedAttempts =
            (notification.getAttempts() == null ? 0 : notification.getAttempts()) + 1;
        notification.setAttempts(updatedAttempts);
        notification.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= properties.getMaxAttempts()) {
          notification.setStatus(DiscordNotificationStatus.FAILED);
        }
        log.error("Failed to dispatch Discord notification {}", notification.getId(), e);
      }
    }
  }

  /** Alias for {@link #run()} retained for backward compatibility. */
  public void poll() {
    run();
  }
}
