package com.chrima.notification.discord.dlq.service;

import com.chrima.notification.discord.dlq.config.DiscordDeadLetterProperties;
import com.chrima.notification.discord.dlq.model.DiscordDeadLetterNotification;
import com.chrima.notification.discord.dlq.model.enums.DiscordDeadLetterStatus;
import com.chrima.notification.discord.dlq.repository.DiscordDeadLetterNotificationRepository;
import com.chrima.notification.discord.model.DiscordNotification;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class DiscordDeadLetterService {

  private final DiscordDeadLetterNotificationRepository discordDeadLetterNotificationRepository;
  private final DiscordDeadLetterProperties properties;

  @Transactional
  public DiscordDeadLetterNotification enqueue(
      DiscordNotification notification, String failureReason) {
    Instant nextAttemptAt = Instant.now().plus(properties.getInitialDelay());
    DiscordDeadLetterNotification deadLetter =
        DiscordDeadLetterNotification.builder()
            .discordNotificationId(notification.getId())
            .guildId(notification.getGuildId())
            .channelId(notification.getChannelId())
            .type(notification.getType())
            .content(notification.getContent())
            .idempotencyKey(notification.getIdempotencyKey())
            .failureReason(failureReason)
            .attempts(0)
            .status(DiscordDeadLetterStatus.PENDING)
            .nextAttemptAt(nextAttemptAt)
            .build();
    return discordDeadLetterNotificationRepository.save(deadLetter);
  }
}
