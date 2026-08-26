package com.chrima.notification.discord.service;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.channel.DiscordNotificationChannel;
import com.chrima.notification.discord.config.DiscordPollingProperties;
import com.chrima.notification.discord.dlq.service.DiscordDeadLetterService;
import com.chrima.notification.discord.model.DiscordNotification;
import com.chrima.notification.discord.model.DiscordNotificationContentRegistry;
import com.chrima.notification.discord.model.enums.DiscordNotificationStatus;
import com.chrima.notification.discord.repository.DiscordNotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.instrumentation.annotations.WithSpan;
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
  private final DiscordDeadLetterService discordDeadLetterService;

  @Scheduled(
      fixedDelayString = "${discord.polling.fixed-delay}",
      initialDelayString = "${discord.polling.initial-delay}")
  @Transactional
  @WithSpan
  public void run() {
    List<DiscordNotification> pending =
        discordNotificationRepository.findPending(PageRequest.of(0, properties.getBatchSize()));

    if (pending.isEmpty()) {
      log.debug(
          "Discord poller - no pending notifications batchSize={}", properties.getBatchSize());
      return;
    }

    log.info(
        "Discord poller - processing batch size={} maxAttempts={}",
        pending.size(),
        properties.getMaxAttempts());

    for (DiscordNotification notification : pending) {
      log.debug(
          "Dispatching Discord notification id={} guildId={} channelId={} type={} attempt={}/{}",
          notification.getId(),
          notification.getGuildId(),
          notification.getChannelId(),
          notification.getType(),
          notification.getAttempts() == null ? 1 : notification.getAttempts() + 1,
          properties.getMaxAttempts());
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
        log.info(
            "Discord notification dispatched id={} guildId={} channelId={} type={} discordMessageId={} attempts={}",
            notification.getId(),
            notification.getGuildId(),
            notification.getChannelId(),
            notification.getType(),
            discordMessageId,
            updatedAttempts);
      } catch (Exception e) {
        int updatedAttempts =
            (notification.getAttempts() == null ? 0 : notification.getAttempts()) + 1;
        notification.setAttempts(updatedAttempts);
        notification.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= properties.getMaxAttempts()) {
          notification.setStatus(DiscordNotificationStatus.FAILED);
          log.warn(
              "Discord notification id={} type={} reached maxAttempts={} - moving to DLQ",
              notification.getId(),
              notification.getType(),
              properties.getMaxAttempts());
          try {
            discordDeadLetterService.enqueue(notification, e.getMessage());
            log.info(
                "Discord notification id={} enqueued to DLQ idempotencyKey={}",
                notification.getId(),
                notification.getIdempotencyKey());
          } catch (Exception dlqEx) {
            log.error(
                "Failed to enqueue Discord notification {} to DLQ", notification.getId(), dlqEx);
          }
        } else {
          log.warn(
              "Failed to dispatch Discord notification id={} type={} attempt={}/{} - will retry",
              notification.getId(),
              notification.getType(),
              updatedAttempts,
              properties.getMaxAttempts(),
              e);
        }
        log.error("Failed to dispatch Discord notification {}", notification.getId(), e);
      }
    }

    log.info("Discord poller - batch completed processed={}", pending.size());
  }

  /** Alias for {@link #run()} retained for backward compatibility. */
  public void poll() {
    run();
  }
}
