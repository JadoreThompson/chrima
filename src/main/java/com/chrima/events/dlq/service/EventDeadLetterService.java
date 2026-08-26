package com.chrima.events.dlq.service;

import com.chrima.events.dlq.config.EventDeadLetterProperties;
import com.chrima.events.dlq.model.EventDeadLetter;
import com.chrima.events.dlq.model.enums.EventDeadLetterStatus;
import com.chrima.events.dlq.repository.EventDeadLetterRepository;
import com.chrima.events.model.EventOutbox;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class EventDeadLetterService {

  private final EventDeadLetterRepository eventDeadLetterRepository;
  private final EventDeadLetterProperties properties;

  @Transactional
  public EventDeadLetter enqueue(EventOutbox event, String failureReason) {
    log.info(
        "Enqueueing event to DLQ id={} eventType={} failureReason='{}'",
        event.getId(),
        event.getEventType(),
        failureReason);
    Instant nextAttemptAt = Instant.now().plus(properties.getInitialDelay());
    EventDeadLetter deadLetter =
        EventDeadLetter.builder()
            .eventOutboxId(event.getId())
            .eventType(event.getEventType())
            .payload(event.getPayload())
            .idempotencyKey(event.getIdempotencyKey())
            .failureReason(failureReason)
            .attempts(0)
            .status(EventDeadLetterStatus.PENDING)
            .nextAttemptAt(nextAttemptAt)
            .build();
    EventDeadLetter saved = eventDeadLetterRepository.save(deadLetter);
    log.info(
        "Event DLQ entry created id={} eventOutboxId={} nextAttemptAt={}",
        saved.getId(),
        event.getId(),
        nextAttemptAt);
    return saved;
  }
}
