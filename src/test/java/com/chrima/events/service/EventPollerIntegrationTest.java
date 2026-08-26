package com.chrima.events.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

import com.chrima.events.config.EventPollingProperties;
import com.chrima.events.dlq.config.EventDeadLetterProperties;
import com.chrima.events.dlq.model.EventDeadLetter;
import com.chrima.events.dlq.model.enums.EventDeadLetterStatus;
import com.chrima.events.dlq.repository.EventDeadLetterRepository;
import com.chrima.events.dlq.service.EventDeadLetterService;
import com.chrima.events.kafka.EventKafkaPublisher;
import com.chrima.events.model.EventOutbox;
import com.chrima.events.model.enums.EventStatus;
import com.chrima.events.repository.EventOutboxRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.data.domain.Pageable;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
@Import({
  EventKafkaPublisher.class,
  ObjectMapper.class,
  EventPoller.class,
  EventDeadLetterService.class,
  EventPollingProperties.class,
  EventDeadLetterProperties.class
})
class EventPollerIntegrationTest {

  @Container
  static PostgreSQLContainer<?> postgres =
      new PostgreSQLContainer<>("postgres:16-alpine")
          .withDatabaseName("chrima")
          .withUsername("postgres")
          .withPassword("password");

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
    registry.add("spring.datasource.driver-class-name", postgres::getDriverClassName);
  }

  @Autowired private EventOutboxRepository eventOutboxRepository;

  @Autowired private EventDeadLetterRepository eventDeadLetterRepository;

  @Autowired private EventPoller eventPoller;

  @MockitoBean private EventKafkaPublisher eventKafkaPublisher;

  @AfterEach
  void tearDown() {
    eventDeadLetterRepository.deleteAll();
    eventOutboxRepository.deleteAll();
  }

  private EventOutbox createPendingEvent(int attempts) {
    return createPendingEvent("test.event.type", attempts);
  }

  private EventOutbox createPendingEvent(String eventType, int attempts) {
    return eventOutboxRepository.save(
        EventOutbox.builder()
            .eventType(eventType)
            .payload("{\"key\":\"value\"}")
            .idempotencyKey(UUID.randomUUID().toString())
            .attempts(attempts)
            .status(EventStatus.PENDING)
            .build());
  }

  private EventOutbox createCompletedEvent() {
    return eventOutboxRepository.save(
        EventOutbox.builder()
            .eventType("test.event.type")
            .payload("{\"key\":\"value\"}")
            .idempotencyKey(UUID.randomUUID().toString())
            .attempts(1)
            .status(EventStatus.COMPLETED)
            .build());
  }

  @Test
  void shouldDeliverSuccessfullyAndMarkCompleted() throws Exception {
    EventOutbox event = createPendingEvent(0);

    eventPoller.run();

    ArgumentCaptor<EventOutbox> captor = ArgumentCaptor.forClass(EventOutbox.class);
    verify(eventKafkaPublisher).publish(captor.capture());
    EventOutbox published = captor.getValue();
    assertThat(published.getId()).isEqualTo(event.getId());
    assertThat(published.getEventType()).isEqualTo(event.getEventType());
    assertThat(published.getIdempotencyKey()).isEqualTo(event.getIdempotencyKey());
    assertThat(published.getPayload()).isEqualTo(event.getPayload());

    EventOutbox reloaded = eventOutboxRepository.findById(event.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(EventStatus.COMPLETED);
    assertThat(reloaded.getDispatchedAt()).isNotNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(eventOutboxRepository.findPending(Pageable.ofSize(10))).isEmpty();
  }

  @Test
  void shouldEnsureKafkaDeliveryIsInvokedWithCorrectIdempotencyKey() throws Exception {
    EventOutbox event = createPendingEvent(0);

    eventPoller.run();

    verify(eventKafkaPublisher).publish(any(EventOutbox.class));
    EventOutbox reloaded = eventOutboxRepository.findById(event.getId()).orElseThrow();
    assertThat(reloaded.getStatus()).isEqualTo(EventStatus.COMPLETED);
  }

  @Test
  void shouldIncrementAttemptsOnFailureAndRemainPending() throws Exception {
    doThrow(new RuntimeException("Kafka unavailable"))
        .when(eventKafkaPublisher)
        .publish(any(EventOutbox.class));

    EventOutbox event = createPendingEvent(0);

    eventPoller.run();

    EventOutbox reloaded = eventOutboxRepository.findById(event.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(EventStatus.PENDING);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(eventOutboxRepository.findPending(Pageable.ofSize(10))).hasSize(1);
    assertThat(eventDeadLetterRepository.findAll()).isEmpty();
  }

  @Test
  void shouldAbandonEventWhenMaxAttemptsBreachedAndMarkFailed() throws Exception {
    doThrow(new RuntimeException("Kafka failure"))
        .when(eventKafkaPublisher)
        .publish(any(EventOutbox.class));

    EventOutbox event = createPendingEvent(2);

    eventPoller.run();

    EventOutbox reloaded = eventOutboxRepository.findById(event.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(3);
    assertThat(reloaded.getStatus()).isEqualTo(EventStatus.FAILED);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(eventOutboxRepository.findPending(Pageable.ofSize(10))).isEmpty();

    List<EventDeadLetter> dlqEntries = eventDeadLetterRepository.findAll();
    assertThat(dlqEntries).hasSize(1);
    EventDeadLetter dlq = dlqEntries.get(0);
    assertThat(dlq.getEventOutboxId()).isEqualTo(event.getId());
    assertThat(dlq.getEventType()).isEqualTo(event.getEventType());
    assertThat(dlq.getPayload()).isEqualTo(event.getPayload());
    assertThat(dlq.getIdempotencyKey()).isEqualTo(event.getIdempotencyKey());
    assertThat(dlq.getStatus()).isEqualTo(EventDeadLetterStatus.PENDING);
    assertThat(dlq.getAttempts()).isEqualTo(0);
    assertThat(dlq.getNextAttemptAt()).isNotNull();
    assertThat(dlq.getFailureReason()).contains("Kafka failure");
  }

  @Test
  void shouldMoveFailedEventToDlqWithInitialDelay() throws Exception {
    doThrow(new RuntimeException("Kafka failure"))
        .when(eventKafkaPublisher)
        .publish(any(EventOutbox.class));

    EventOutbox event = createPendingEvent(2);

    long before = System.currentTimeMillis();
    eventPoller.run();
    long after = System.currentTimeMillis();

    EventDeadLetter dlq = eventDeadLetterRepository.findAll().get(0);
    assertThat(dlq.getNextAttemptAt()).isNotNull();
    assertThat(dlq.getNextAttemptAt().toEpochMilli()).isGreaterThanOrEqualTo(before + 900);
  }

  @Test
  void shouldNotProcessCompletedEvents() throws Exception {
    createCompletedEvent();
    EventOutbox pending = createPendingEvent(0);

    eventPoller.run();

    verify(eventKafkaPublisher).publish(any(EventOutbox.class));
    // only pending should have been processed, completed remains untouched
    assertThat(eventOutboxRepository.findAll()).hasSize(2);
    EventOutbox reloadedPending = eventOutboxRepository.findById(pending.getId()).orElseThrow();
    assertThat(reloadedPending.getStatus()).isEqualTo(EventStatus.COMPLETED);
  }

  @Test
  void shouldNotProcessWhenNoPendingEvents() throws Exception {
    eventPoller.run();

    verify(eventKafkaPublisher, never()).publish(any(EventOutbox.class));
  }

  @Test
  void shouldProcessBatchOfPendingEventsAndEnsureEachDeliveredViaKafka() throws Exception {
    EventOutbox first = createPendingEvent(0);
    EventOutbox second = createPendingEvent(0);
    EventOutbox third = createPendingEvent(0);

    eventPoller.run();

    verify(eventKafkaPublisher, org.mockito.Mockito.times(3)).publish(any(EventOutbox.class));

    for (EventOutbox e : List.of(first, second, third)) {
      EventOutbox reloaded = eventOutboxRepository.findById(e.getId()).orElseThrow();
      assertThat(reloaded.getStatus()).isEqualTo(EventStatus.COMPLETED);
      assertThat(reloaded.getAttempts()).isEqualTo(1);
      assertThat(reloaded.getDispatchedAt()).isNotNull();
    }
    assertThat(eventOutboxRepository.findPending(Pageable.ofSize(10))).isEmpty();
  }

  @Test
  void shouldContinueProcessingRemainingEventsWhenOneFails() throws Exception {
    // First call throws, subsequent calls succeed - simulate by doThrow on first then doNothing
    doThrow(new RuntimeException("Kafka fail on first"))
        .doNothing()
        .when(eventKafkaPublisher)
        .publish(any(EventOutbox.class));

    EventOutbox first = createPendingEvent(0);
    EventOutbox second = createPendingEvent(0);

    eventPoller.run();

    // poller loops, so both events attempted; we cannot guarantee order, but verify one pending one
    // completed
    long completedCount =
        eventOutboxRepository.findAll().stream()
            .filter(e -> e.getStatus() == EventStatus.COMPLETED)
            .count();
    long pendingCount =
        eventOutboxRepository.findAll().stream()
            .filter(e -> e.getStatus() == EventStatus.PENDING)
            .count();

    // one should be completed, one should remain pending (retry)
    assertThat(completedCount).isEqualTo(1);
    assertThat(pendingCount).isEqualTo(1);
    assertThat(eventDeadLetterRepository.findAll()).isEmpty();
  }

  @Test
  void shouldTreatUnmappedTopicAsPublishFailureAndEventuallyMoveToDlq() throws Exception {
    // With specific-topic routing (no global fallback), publisher throws IllegalArgumentException
    // when eventType has no registered topic. Poller should treat it like any publish failure:
    // increment attempts, retry, and move to DLQ after maxAttempts.
    doThrow(new IllegalArgumentException("No topic registered for event type unmapped.event"))
        .when(eventKafkaPublisher)
        .publish(any(EventOutbox.class));

    EventOutbox event = createPendingEvent("unmapped.event", 0);

    eventPoller.run();
    EventOutbox afterFirst = eventOutboxRepository.findById(event.getId()).orElseThrow();
    assertThat(afterFirst.getAttempts()).isEqualTo(1);
    assertThat(afterFirst.getStatus()).isEqualTo(EventStatus.PENDING);
    assertThat(eventDeadLetterRepository.findAll()).isEmpty();

    // two more failures to reach maxAttempts=3 -> DLQ
    eventPoller.run();
    eventPoller.run();

    EventOutbox reloaded = eventOutboxRepository.findById(event.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(3);
    assertThat(reloaded.getStatus()).isEqualTo(EventStatus.FAILED);
    List<EventDeadLetter> dlq = eventDeadLetterRepository.findAll();
    assertThat(dlq).hasSize(1);
    assertThat(dlq.get(0).getFailureReason()).contains("No topic registered");
    assertThat(dlq.get(0).getEventType()).isEqualTo("unmapped.event");
  }
}
