package com.chrima.notification.dlq.service;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.EmailNotificationContent;
import com.chrima.notification.channel.INotificationChannel;
import com.chrima.notification.dlq.config.DeadLetterPollingProperties;
import com.chrima.notification.dlq.model.DeadLetterNotification;
import com.chrima.notification.dlq.model.enums.DeadLetterStatus;
import com.chrima.notification.dlq.repository.DeadLetterNotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.instrumentation.annotations.WithSpan;
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
  private final DeadLetterPollingProperties properties;
  private final List<INotificationChannel<?>> notificationChannels;
  private final ObjectMapper objectMapper;

  @Scheduled(fixedDelayString = "${notification.dlq.polling-delay:5000}")
  @Transactional
  @WithSpan
  public void run() {
    List<DeadLetterNotification> entries =
        deadLetterNotificationRepository.findReady(
            Instant.now(), Pageable.ofSize(properties.getBatchSize()));

    if (entries.isEmpty()) {
      log.debug("DLQ poller - no ready entries batchSize={}", properties.getBatchSize());
      return;
    }

    log.info(
        "DLQ poller - processing batch size={} maxAttempts={}",
        entries.size(),
        properties.getMaxAttempts());

    for (DeadLetterNotification entry : entries) {
      log.debug(
          "Retrying DLQ entry id={} notificationId={} channel={} attempt={}/{}",
          entry.getId(),
          entry.getNotificationId(),
          entry.getChannel(),
          entry.getAttempts() == null ? 1 : entry.getAttempts() + 1,
          properties.getMaxAttempts());
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
        log.info(
            "DLQ entry dispatched id={} notificationId={} channel={} attempts={}",
            entry.getId(),
            entry.getNotificationId(),
            entry.getChannel(),
            updatedAttempts);
      } catch (Exception e) {
        int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
        entry.setAttempts(updatedAttempts);
        entry.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= properties.getMaxAttempts()) {
          entry.setStatus(DeadLetterStatus.FAILED);
          log.warn(
              "DLQ entry id={} permanently failed after {}/{} attempts channel={}",
              entry.getId(),
              updatedAttempts,
              properties.getMaxAttempts(),
              entry.getChannel());
        } else {
          Instant nextAttempt = calculateNextAttempt(updatedAttempts);
          entry.setNextAttemptAt(nextAttempt);
          log.warn(
              "DLQ retry failed id={} channel={} attempt={}/{} nextAttemptAt={}",
              entry.getId(),
              entry.getChannel(),
              updatedAttempts,
              properties.getMaxAttempts(),
              nextAttempt,
              e);
        }
        if (e instanceof NoSuchElementException) {
          log.warn("No implementation found for DLQ channel '{}'", entry.getChannel(), e);
        } else {
          log.error("Failed to dispatch DLQ notification {}", entry.getId(), e);
        }
      }
    }

    log.info("DLQ poller - batch completed processed={}", entries.size());
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
