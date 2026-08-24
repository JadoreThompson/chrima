package com.chrima.notification.discord.dlq.service;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.channel.DiscordNotificationChannel;
import com.chrima.notification.discord.dlq.config.DiscordDeadLetterProperties;
import com.chrima.notification.discord.dlq.model.DiscordDeadLetterNotification;
import com.chrima.notification.discord.dlq.model.enums.DiscordDeadLetterStatus;
import com.chrima.notification.discord.dlq.repository.DiscordDeadLetterNotificationRepository;
import com.chrima.notification.discord.model.DiscordNotificationContentRegistry;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.NoSuchElementException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
public class DiscordDeadLetterPoller {

  private final DiscordDeadLetterNotificationRepository discordDeadLetterNotificationRepository;
  private final DiscordDeadLetterProperties properties;
  private final DiscordNotificationChannel discordNotificationChannel;
  private final ObjectMapper objectMapper;
  private final DiscordNotificationContentRegistry registry;

  @Scheduled(fixedDelayString = "${discord.dlq.polling-delay:5000}")
  @Transactional
  public void run() {
    List<DiscordDeadLetterNotification> entries =
        discordDeadLetterNotificationRepository.findReady(
            Instant.now(), Pageable.ofSize(properties.getBatchSize()));

    for (DiscordDeadLetterNotification entry : entries) {
      try {
        IDiscordNotificationContent content =
            objectMapper.readValue(entry.getContent(), registry.get(entry.getType()));
        Long discordMessageId =
            discordNotificationChannel.send(
                entry.getGuildId(), entry.getChannelId(), content, entry.getIdempotencyKey());

        int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
        entry.setAttempts(updatedAttempts);
        entry.setLastAttemptedAt(Instant.now());
        entry.markDispatched();
        // Optionally store discordMessageId if needed; dispatchedAt tracks success
        entry.setStatus(DiscordDeadLetterStatus.COMPLETED);
        log.debug(
            "Dispatched Discord DLQ notification {} with discordMessageId {}",
            entry.getId(),
            discordMessageId);
      } catch (Exception e) {
        int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
        entry.setAttempts(updatedAttempts);
        entry.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= properties.getMaxAttempts()) {
          entry.setStatus(DiscordDeadLetterStatus.FAILED);
        } else {
          Instant nextAttempt = calculateNextAttempt(updatedAttempts);
          entry.setNextAttemptAt(nextAttempt);
        }
        if (e instanceof NoSuchElementException) {
          log.warn("No implementation found for Discord DLQ type '{}'", entry.getType(), e);
        } else {
          log.error("Failed to dispatch Discord DLQ notification {}", entry.getId(), e);
        }
      }
    }
  }

  public Instant calculateNextAttempt(int attempts) {
    return calculateNextAttempt(attempts, Instant.now());
  }

  public Instant calculateNextAttempt(int attempts, Instant now) {
    Duration initialDelay = properties.getInitialDelay();
    double multiplier = properties.getBackoffMultiplier();
    long delayMillis = (long) (initialDelay.toMillis() * Math.pow(multiplier, attempts - 1));
    if (attempts <= 1) {
      delayMillis = initialDelay.toMillis();
    }
    return now.plusMillis(delayMillis);
  }
}
