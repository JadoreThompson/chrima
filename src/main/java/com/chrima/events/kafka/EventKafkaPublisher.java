package com.chrima.events.kafka;

import com.chrima.events.dlq.model.EventDeadLetter;
import com.chrima.events.model.EventOutbox;
import com.chrima.events.model.EventTopicRegistry;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class EventKafkaPublisher {

  private final KafkaTemplate<String, String> kafkaTemplate;
  private final EventTopicRegistry topicRegistry;

  @WithSpan
  public void publish(
      @SpanAttribute("event.id") String id,
      @SpanAttribute("event.type") String eventType,
      @SpanAttribute("event.idempotency_key") String idempotencyKey,
      String payload)
      throws Exception {
    String topic = topicRegistry.getTopic(eventType);
    ProducerRecord<String, String> record = new ProducerRecord<>(topic, idempotencyKey, payload);
    record.headers().add("eventType", eventType.getBytes(StandardCharsets.UTF_8));
    record.headers().add("idempotencyKey", idempotencyKey.getBytes(StandardCharsets.UTF_8));
    if (id != null) {
      record.headers().add("eventId", id.getBytes(StandardCharsets.UTF_8));
    }
    log.info(
        "Publishing event to kafka topic={} key={} eventType={} idempotencyKey={}",
        topic,
        idempotencyKey,
        eventType,
        idempotencyKey);
    kafkaTemplate.send(record).get(10, TimeUnit.SECONDS);
    log.info(
        "Event published to kafka topic={} key={} eventType={} idempotencyKey={}",
        topic,
        idempotencyKey,
        eventType,
        idempotencyKey);
  }

  public void publish(EventOutbox event) throws Exception {
    publish(
        event.getId() != null ? event.getId().toString() : null,
        event.getEventType(),
        event.getIdempotencyKey(),
        event.getPayload());
  }

  public void publish(EventDeadLetter event) throws Exception {
    publish(
        event.getId() != null ? event.getId().toString() : null,
        event.getEventType(),
        event.getIdempotencyKey(),
        event.getPayload());
  }
}
