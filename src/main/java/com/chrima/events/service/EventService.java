package com.chrima.events.service;

import com.chrima.events.api.IEventService;
import com.chrima.events.api.model.IEventPayload;
import com.chrima.events.model.EventOutbox;
import com.chrima.events.model.EventTopicRegistry;
import com.chrima.events.repository.EventOutboxRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class EventService implements IEventService {

  private final EventOutboxRepository eventOutboxRepository;
  private final ObjectMapper objectMapper;
  private final EventTopicRegistry eventTopicRegistry;

  @Override
  @Transactional
  @WithSpan
  public void publish(
      @SpanAttribute("event.type") String eventType,
      IEventPayload payload,
      @SpanAttribute("event.idempotency_key") String idempotencyKey)
      throws IOException {
    log.info("Publishing event eventType={} idempotencyKey={}", eventType, idempotencyKey);
    if (eventType == null || eventType.isBlank()) {
      log.warn("Event publish rejected - eventType must not be blank");
      throw new IllegalArgumentException("eventType must not be blank");
    }
    if (!eventTopicRegistry.contains(eventType)) {
      log.warn("Event publish rejected - topic for eventType does not exist");
      throw new IllegalArgumentException("topic for eventType does not exist");
    }
    if (idempotencyKey == null || idempotencyKey.isBlank()) {
      log.warn("Event publish rejected - idempotencyKey must not be blank");
      throw new IllegalArgumentException("idempotencyKey must not be blank");
    }
    if (payload == null) {
      log.warn("Event publish rejected - payload must not be null");
      throw new IllegalArgumentException("payload must not be null");
    }
    if (eventOutboxRepository.existsByIdempotencyKey(idempotencyKey)) {
      log.info("Duplicate event ignored idempotencyKey={} eventType={}", idempotencyKey, eventType);
      return;
    }

    EventOutbox saved =
        eventOutboxRepository.save(
            EventOutbox.builder()
                .eventType(eventType)
                .payload(objectMapper.writeValueAsString(payload))
                .idempotencyKey(idempotencyKey)
                .build());
    log.info(
        "Event enqueued id={} eventType={} idempotencyKey={}",
        saved.getId(),
        eventType,
        idempotencyKey);
  }
}
