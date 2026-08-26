package com.chrima.events.service;

import com.chrima.events.config.EventPollingProperties;
import com.chrima.events.dlq.service.EventDeadLetterService;
import com.chrima.events.kafka.EventKafkaPublisher;
import com.chrima.events.model.EventOutbox;
import com.chrima.events.model.enums.EventStatus;
import com.chrima.events.repository.EventOutboxRepository;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import java.time.Instant;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
public class EventPoller {

  private final EventOutboxRepository eventOutboxRepository;
  private final EventKafkaPublisher eventKafkaPublisher;
  private final EventDeadLetterService eventDeadLetterService;
  private final EventPollingProperties properties;

  @Scheduled(fixedDelayString = "${events.polling.delay:5000}")
  @Transactional
  @WithSpan
  public void run() {
    List<EventOutbox> pending =
        eventOutboxRepository.findPending(PageRequest.of(0, properties.getBatchSize()));

    if (pending.isEmpty()) {
      log.debug("Event poller - no pending events batchSize={}", properties.getBatchSize());
      return;
    }

    log.info(
        "Event poller - processing batch size={} maxAttempts={}",
        pending.size(),
        properties.getMaxAttempts());

    for (EventOutbox event : pending) {
      log.debug(
          "Dispatching event id={} eventType={} attempt={}/{}",
          event.getId(),
          event.getEventType(),
          event.getAttempts() == null ? 1 : event.getAttempts() + 1,
          properties.getMaxAttempts());
      try {
        eventKafkaPublisher.publish(event);

        int updatedAttempts = (event.getAttempts() == null ? 0 : event.getAttempts()) + 1;
        event.setAttempts(updatedAttempts);
        event.setLastAttemptedAt(Instant.now());
        event.markDispatched();
        event.setStatus(EventStatus.COMPLETED);
        log.info(
            "Event dispatched to kafka id={} eventType={} attempts={}",
            event.getId(),
            event.getEventType(),
            updatedAttempts);
      } catch (Exception e) {
        int updatedAttempts = (event.getAttempts() == null ? 0 : event.getAttempts()) + 1;
        event.setAttempts(updatedAttempts);
        event.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= properties.getMaxAttempts()) {
          event.setStatus(EventStatus.FAILED);
          log.warn(
              "Event id={} eventType={} reached maxAttempts={} - moving to DLQ",
              event.getId(),
              event.getEventType(),
              properties.getMaxAttempts());
          try {
            eventDeadLetterService.enqueue(event, e.getMessage());
            log.info(
                "Event id={} enqueued to DLQ idempotencyKey={}",
                event.getId(),
                event.getIdempotencyKey());
          } catch (Exception dlqEx) {
            log.error("Failed to enqueue event {} to DLQ", event.getId(), dlqEx);
          }
        } else {
          log.warn(
              "Failed to publish event to kafka id={} eventType={} attempt={}/{} - will retry",
              event.getId(),
              event.getEventType(),
              updatedAttempts,
              properties.getMaxAttempts(),
              e);
        }
        log.error("Failed to dispatch event {}", event.getId(), e);
      }
    }

    log.info("Event poller - batch completed processed={}", pending.size());
  }

  /** Alias for {@link #run()} retained for backward compatibility and testing convenience. */
  public void poll() {
    run();
  }
}
