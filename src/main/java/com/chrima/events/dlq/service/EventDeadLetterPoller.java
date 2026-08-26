package com.chrima.events.dlq.service;

import com.chrima.events.dlq.config.EventDeadLetterProperties;
import com.chrima.events.dlq.model.EventDeadLetter;
import com.chrima.events.dlq.model.enums.EventDeadLetterStatus;
import com.chrima.events.dlq.repository.EventDeadLetterRepository;
import com.chrima.events.kafka.EventKafkaPublisher;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
public class EventDeadLetterPoller {

  private final EventDeadLetterRepository eventDeadLetterRepository;
  private final EventDeadLetterProperties properties;
  private final EventKafkaPublisher eventKafkaPublisher;

  @Scheduled(fixedDelayString = "${events.dlq.polling-delay:5000}")
  @Transactional
  @WithSpan
  public void run() {
    List<EventDeadLetter> entries =
        eventDeadLetterRepository.findReady(
            Instant.now(), Pageable.ofSize(properties.getBatchSize()));

    if (entries.isEmpty()) {
      log.debug("Event DLQ poller - no ready entries batchSize={}", properties.getBatchSize());
      return;
    }

    log.info(
        "Event DLQ poller - processing batch size={} maxAttempts={}",
        entries.size(),
        properties.getMaxAttempts());

    for (EventDeadLetter entry : entries) {
      log.debug(
          "Retrying Event DLQ entry id={} eventOutboxId={} eventType={} attempt={}/{}",
          entry.getId(),
          entry.getEventOutboxId(),
          entry.getEventType(),
          entry.getAttempts() == null ? 1 : entry.getAttempts() + 1,
          properties.getMaxAttempts());
      try {
        eventKafkaPublisher.publish(entry);

        int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
        entry.setAttempts(updatedAttempts);
        entry.setLastAttemptedAt(Instant.now());
        entry.markDispatched();
        entry.setStatus(EventDeadLetterStatus.COMPLETED);
        log.info(
            "Event DLQ entry dispatched to kafka id={} eventOutboxId={} eventType={} attempts={}",
            entry.getId(),
            entry.getEventOutboxId(),
            entry.getEventType(),
            updatedAttempts);
      } catch (Exception e) {
        int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
        entry.setAttempts(updatedAttempts);
        entry.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= properties.getMaxAttempts()) {
          entry.setStatus(EventDeadLetterStatus.FAILED);
          log.warn(
              "Event DLQ entry id={} permanently failed after {}/{} attempts eventType={}",
              entry.getId(),
              updatedAttempts,
              properties.getMaxAttempts(),
              entry.getEventType());
        } else {
          Instant nextAttempt = calculateNextAttempt(updatedAttempts);
          entry.setNextAttemptAt(nextAttempt);
          log.warn(
              "Event DLQ retry failed id={} eventType={} attempt={}/{} nextAttemptAt={}",
              entry.getId(),
              entry.getEventType(),
              updatedAttempts,
              properties.getMaxAttempts(),
              nextAttempt,
              e);
        }
        log.error("Failed to dispatch Event DLQ entry {}", entry.getId(), e);
      }
    }

    log.info("Event DLQ poller - batch completed processed={}", entries.size());
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
