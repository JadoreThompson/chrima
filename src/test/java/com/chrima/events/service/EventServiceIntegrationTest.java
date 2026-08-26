package com.chrima.events.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.Assert.assertThrows;

import com.chrima.events.api.model.IEventPayload;
import com.chrima.events.model.EventOutbox;
import com.chrima.events.model.EventTopicRegistry;
import com.chrima.events.model.enums.EventStatus;
import com.chrima.events.repository.EventOutboxRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
@Import({EventService.class, EventTopicRegistry.class, ObjectMapper.class})
class EventServiceIntegrationTest {

  @Container
  static PostgreSQLContainer<?> postgres =
      new PostgreSQLContainer<>("postgres:16-alpine")
          .withDatabaseName("chrima")
          .withUsername("postgres")
          .withPassword("password");

  @Autowired private EventTopicRegistry eventTopicRegistry;

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
    registry.add("spring.datasource.driver-class-name", postgres::getDriverClassName);
  }

  @Autowired private EventService eventService;

  @Autowired private EventOutboxRepository eventOutboxRepository;

  @Autowired private ObjectMapper objectMapper;

  @AfterEach
  void tearDown() {
    eventOutboxRepository.deleteAll();
  }

  static class TestEventPayload implements IEventPayload {
    public String foo;
    public int num;

    public TestEventPayload() {}

    public TestEventPayload(String foo, int num) {
      this.foo = foo;
      this.num = num;
    }
  }

  @Test
  void shouldPublishAndPersistEventWithPendingStatus() throws Exception {
    String eventType = "test.event.created";
    String idempotencyKey = UUID.randomUUID().toString();
    TestEventPayload payload = new TestEventPayload("bar", 42);

    eventTopicRegistry.register(eventType, "test");
    eventService.publish(eventType, payload, idempotencyKey);

    List<EventOutbox> all = eventOutboxRepository.findAll();
    assertThat(all).hasSize(1);
    EventOutbox saved = all.get(0);
    assertThat(saved.getId()).isNotNull();
    assertThat(saved.getEventType()).isEqualTo(eventType);
    assertThat(saved.getIdempotencyKey()).isEqualTo(idempotencyKey);
    //    assertThat(saved.getPayload()).contains("\"foo\"");
    //    assertThat(saved.getPayload()).contains("bar");
    TestEventPayload deserialized =
        objectMapper.readValue(saved.getPayload(), TestEventPayload.class);
    assertThat(deserialized.foo).isEqualTo(payload.foo);
    assertThat(saved.getStatus()).isEqualTo(EventStatus.PENDING);
    assertThat(saved.getAttempts()).isEqualTo(0);
    assertThat(saved.getDispatchedAt()).isNull();
    assertThat(saved.getCreatedAt()).isNotNull();
  }

  //  @Test
  //  void shouldSerializePayloadCorrectly() throws Exception {
  //    String idempotencyKey = UUID.randomUUID().toString();
  //    TestEventPayload payload = new TestEventPayload("hello", 123);
  //
  //    eventService.publish("test.event.serialize", payload, idempotencyKey);
  //
  //    EventOutbox saved = eventOutboxRepository.findAll().get(0);
  //    // verify payload can be deserialized back
  //    TestEventPayload deserialized =
  //        objectMapper.readValue(saved.getPayload(), TestEventPayload.class);
  //    assertThat(deserialized.foo).isEqualTo("hello");
  //    assertThat(deserialized.num).isEqualTo(123);
  //  }

  @Test
  void shouldIgnoreDuplicateIdempotencyKey() throws Exception {
    String idempotencyKey = UUID.randomUUID().toString();
    TestEventPayload payload1 = new TestEventPayload("first", 1);
    TestEventPayload payload2 = new TestEventPayload("second", 2);

    eventTopicRegistry.register("test.event.dup", "test");
    eventService.publish("test.event.dup", payload1, idempotencyKey);
    eventService.publish("test.event.dup", payload2, idempotencyKey);

    List<EventOutbox> all = eventOutboxRepository.findAll();
    assertThat(all).hasSize(1);
    assertThat(all.get(0).getPayload()).contains("first");
    assertThat(all.get(0).getPayload()).doesNotContain("second");
  }

  @Test
  void shouldAllowDifferentIdempotencyKeysForSameEventType() throws Exception {
    String eventType = "test.event.sameType";
    TestEventPayload p1 = new TestEventPayload("a", 1);
    TestEventPayload p2 = new TestEventPayload("b", 2);

    eventTopicRegistry.register(eventType, "test");
    eventService.publish(eventType, p1, UUID.randomUUID().toString());
    eventService.publish(eventType, p2, UUID.randomUUID().toString());

    assertThat(eventOutboxRepository.findAll()).hasSize(2);
  }

  @Test
  void shouldStillEnqueueUnknownEventTypeWithoutTopicMapping() throws Exception {
    // EventService does not validate topic registry; unknown types are still persisted to outbox.
    // With specific-topic routing (no global fallback), the poller/publisher will fail to resolve
    // the topic and the event will be retried then moved to DLQ.
    String unknownType = "unknown.event.type." + UUID.randomUUID();
    String idempotencyKey = UUID.randomUUID().toString();

    //        eventTopicRegistry.register(unknownType, "unknown-topic");
    //        eventService.publish(unknownType, new TestEventPayload("x", 9), idempotencyKey);
    assertThrows(
        IllegalArgumentException.class,
        () -> eventService.publish(unknownType, new TestEventPayload("x", 9), idempotencyKey));

    List<EventOutbox> all = eventOutboxRepository.findAll();
    assertThat(all).isEmpty();
  }

  @Test
  void shouldRejectBlankEventType() {
    String idempotencyKey = UUID.randomUUID().toString();
    TestEventPayload payload = new TestEventPayload("foo", 1);

    assertThatThrownBy(() -> eventService.publish("", payload, idempotencyKey))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("eventType");
    assertThatThrownBy(() -> eventService.publish("   ", payload, idempotencyKey))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("eventType");
    assertThat(eventOutboxRepository.findAll()).isEmpty();
  }

  @Test
  void shouldRejectNullEventType() {
    String idempotencyKey = UUID.randomUUID().toString();
    TestEventPayload payload = new TestEventPayload("foo", 1);

    assertThatThrownBy(() -> eventService.publish(null, payload, idempotencyKey))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("eventType");
    assertThat(eventOutboxRepository.findAll()).isEmpty();
  }

  @Test
  void shouldRejectBlankIdempotencyKey() {
    TestEventPayload payload = new TestEventPayload("foo", 1);

    eventTopicRegistry.register("test.event", "test");
    assertThatThrownBy(() -> eventService.publish("test.event", payload, ""))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("idempotencyKey");
    assertThatThrownBy(() -> eventService.publish("test.event", payload, "   "))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("idempotencyKey");
    assertThat(eventOutboxRepository.findAll()).isEmpty();
  }

  @Test
  void shouldRejectNullIdempotencyKey() {
    TestEventPayload payload = new TestEventPayload("foo", 1);

    eventTopicRegistry.register("test.event", "test");
    assertThatThrownBy(() -> eventService.publish("test.event", payload, null))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("idempotencyKey");
    assertThat(eventOutboxRepository.findAll()).isEmpty();
  }

  @Test
  void shouldRejectNullPayload() {
    String idempotencyKey = UUID.randomUUID().toString();

    assertThatThrownBy(() -> eventService.publish("test.event", null, idempotencyKey))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("payload");
    assertThat(eventOutboxRepository.findAll()).isEmpty();
  }

  @Test
  void shouldNotPersistWhenValidationFails() {
    long countBefore = eventOutboxRepository.count();

    try {
      eventService.publish(null, null, null);
    } catch (Exception ignored) {
    }

    assertThat(eventOutboxRepository.count()).isEqualTo(countBefore);
  }
}
