package com.chrima.notification.dlq.service;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.EmailNotificationContent;
import com.chrima.notification.channel.INotificationChannel;
import com.chrima.notification.dlq.config.DeadLetterProperties;
import com.chrima.notification.dlq.model.DeadLetterNotification;
import com.chrima.notification.dlq.model.enums.DeadLetterStatus;
import com.chrima.notification.dlq.repository.DeadLetterNotificationRepository;
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
public class DeadLetterPoller {

  private final DeadLetterNotificationRepository deadLetterNotificationRepository;
  private final DeadLetterProperties properties;
  private final List<INotificationChannel<?>> notificationChannels;
  private final ObjectMapper objectMapper;

  @Scheduled(fixedDelayString = "${notification.dlq.polling-delay:5000}")
  @Transactional
  public void run() {
    List<DeadLetterNotification> entries =
        deadLetterNotificationRepository.findReady(
            Instant.now(), Pageable.ofSize(properties.getBatchSize()));

    for (DeadLetterNotification entry : entries) {
      try {
        INotificationChannel<?> channel =
            notificationChannels.stream()
                .filter(ch -> ch.supports(entry.getChannel()))
                .findFirst()
                .orElseThrow();

        if (entry.getChannel() == ChannelType.EMAIL) {
          EmailNotificationContent content =
              objectMapper.readValue(entry.getContent(), EmailNotificationContent.class);
          @SuppressWarnings("unchecked")
          INotificationChannel<EmailNotificationContent> emailChannel =
              (INotificationChannel<EmailNotificationContent>) channel;
          emailChannel.dispatch(entry.getRecipient(), content);
        } else {
          log.error("Content class for DLQ channel '{}' not found", entry.getChannel());
          throw new IllegalStateException(
              "Content class for DLQ channel '" + entry.getChannel() + "' not found");
        }

        int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
        entry.setAttempts(updatedAttempts);
        entry.setLastAttemptedAt(Instant.now());
        entry.markDispatched();
        entry.setStatus(DeadLetterStatus.COMPLETED);
      } catch (Exception e) {
        int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
        entry.setAttempts(updatedAttempts);
        entry.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= properties.getMaxAttempts()) {
          entry.setStatus(DeadLetterStatus.FAILED);
        } else {
          Instant nextAttempt = calculateNextAttempt(updatedAttempts);
          entry.setNextAttemptAt(nextAttempt);
        }
        if (e instanceof NoSuchElementException) {
          log.warn("No implementation found for DLQ channel '{}'", entry.getChannel(), e);
        } else {
          log.error("Failed to dispatch DLQ notification {}", entry.getId(), e);
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
