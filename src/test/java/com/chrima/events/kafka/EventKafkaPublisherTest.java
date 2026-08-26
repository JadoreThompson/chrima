package com.chrima.events.kafka;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.events.model.EventOutbox;
import com.chrima.events.model.EventTopicRegistry;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.clients.producer.RecordMetadata;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.kafka.core.KafkaTemplate;

@ExtendWith(MockitoExtension.class)
class EventKafkaPublisherTest {

  @Mock private KafkaTemplate<String, String> kafkaTemplate;

  private EventTopicRegistry topicRegistry;
  private EventKafkaPublisher publisher;

  @BeforeEach
  void setUp() {
    topicRegistry =
        new EventTopicRegistry(Map.of("order.created", "orders", "user.registered", "users"));
    publisher = new EventKafkaPublisher(kafkaTemplate, topicRegistry);
  }

  @Test
  void shouldPublishToMappedTopicWithHeaders() throws Exception {
    EventOutbox event =
        EventOutbox.builder()
            .eventType("order.created")
            .payload("{\"orderId\":123}")
            .idempotencyKey("key-123")
            .build();
    // set id via reflection? id is generated, we can set via builder or keep null and verify header
    // handling
    // For publisher, id may be null; we set a UUID via builder by using reflection hack: use save
    // id later
    // Instead test via direct publish method with id
    String eventId = UUID.randomUUID().toString();
    CompletableFuture<RecordMetadata> future = CompletableFuture.completedFuture(null);
    when(kafkaTemplate.send(any(ProducerRecord.class))).thenReturn(future);

    publisher.publish(eventId, "order.created", "key-123", "{\"orderId\":123}");

    ArgumentCaptor<ProducerRecord<String, String>> captor =
        ArgumentCaptor.forClass(ProducerRecord.class);
    verify(kafkaTemplate).send(captor.capture());
    ProducerRecord<String, String> record = captor.getValue();
    assertThat(record.topic()).isEqualTo("orders");
    assertThat(record.key()).isEqualTo("key-123");
    assertThat(record.value()).isEqualTo("{\"orderId\":123}");
    assertThat(new String(record.headers().lastHeader("eventType").value(), StandardCharsets.UTF_8))
        .isEqualTo("order.created");
    assertThat(
            new String(
                record.headers().lastHeader("idempotencyKey").value(), StandardCharsets.UTF_8))
        .isEqualTo("key-123");
    assertThat(new String(record.headers().lastHeader("eventId").value(), StandardCharsets.UTF_8))
        .isEqualTo(eventId);
  }

  @Test
  void shouldThrowWhenEventTypeNotMappedToTopic() {
    assertThatThrownBy(
            () ->
                publisher.publish(
                    UUID.randomUUID().toString(), "unknown.event.type", "key-xyz", "{}"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("No topic registered for event type");
  }

  @Test
  void shouldThrowWhenPublishingOutboxWithUnmappedType() {
    EventOutbox event =
        EventOutbox.builder()
            .eventType("unknown.type")
            .payload("{}")
            .idempotencyKey("idem-999")
            .build();

    assertThatThrownBy(() -> publisher.publish(event))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("No topic registered");
  }

  @Test
  void shouldPublishEventOutboxEntity() throws Exception {
    CompletableFuture<RecordMetadata> future = CompletableFuture.completedFuture(null);
    when(kafkaTemplate.send(any(ProducerRecord.class))).thenReturn(future);

    EventOutbox event =
        EventOutbox.builder()
            .eventType("user.registered")
            .payload("{\"user\":\"alice\"}")
            .idempotencyKey("idem-456")
            .build();
    // force id via builder not set -> null, but publish should still handle null id
    publisher.publish(event);

    ArgumentCaptor<ProducerRecord<String, String>> captor =
        ArgumentCaptor.forClass(ProducerRecord.class);
    verify(kafkaTemplate).send(captor.capture());
    assertThat(captor.getValue().topic()).isEqualTo("users");
    assertThat(captor.getValue().key()).isEqualTo("idem-456");
    // eventId header should be absent when id is null
    assertThat(captor.getValue().headers().lastHeader("eventId")).isNull();
  }

  @Test
  void shouldPropagateExceptionWhenKafkaSendFails() throws Exception {
    CompletableFuture<RecordMetadata> future = new CompletableFuture<>();
    future.completeExceptionally(new RuntimeException("Kafka down"));
    when(kafkaTemplate.send(any(ProducerRecord.class))).thenReturn(future);

    assertThatThrownBy(
            () -> publisher.publish(UUID.randomUUID().toString(), "order.created", "k1", "{}"))
        .isInstanceOf(Exception.class);
  }

  @Test
  void shouldIncludeAllRequiredHeadersAndEnsureDelivery() throws Exception {
    CompletableFuture<RecordMetadata> future = CompletableFuture.completedFuture(null);
    when(kafkaTemplate.send(any(ProducerRecord.class))).thenReturn(future);

    String id = UUID.randomUUID().toString();
    publisher.publish(id, "order.created", "my-key", "{\"a\":1}");

    ArgumentCaptor<ProducerRecord<String, String>> captor =
        ArgumentCaptor.forClass(ProducerRecord.class);
    verify(kafkaTemplate).send(captor.capture());
    ProducerRecord<String, String> record = captor.getValue();
    // verify that exactly three headers are present when id is given
    assertThat(record.headers().toArray()).hasSize(3);
    assertThat(record.headers().lastHeader("eventType")).isNotNull();
    assertThat(record.headers().lastHeader("idempotencyKey")).isNotNull();
    assertThat(record.headers().lastHeader("eventId")).isNotNull();
  }
}
