package com.chrima.events.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.events.model.EventOutbox;
import com.chrima.events.model.enums.EventStatus;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
class EventOutboxRepositoryTest {

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

  @AfterEach
  void tearDown() {
    eventOutboxRepository.deleteAll();
  }

  private EventOutbox save(EventStatus status, Instant dispatchedAt, String idempotencyKey) {
    EventOutbox event =
        EventOutbox.builder()
            .eventType("test.event")
            .payload("{\"k\":\"v\"}")
            .idempotencyKey(idempotencyKey)
            .status(status)
            .attempts(0)
            .build();
    event.setDispatchedAt(dispatchedAt);
    return eventOutboxRepository.save(event);
  }

  private EventOutbox save(EventStatus status, Instant dispatchedAt) {
    return save(status, dispatchedAt, UUID.randomUUID().toString());
  }

  @Test
  void findPendingShouldReturnOnlyPendingWithNullDispatchedAt() {
    EventOutbox pendingUndispatched = save(EventStatus.PENDING, null);
    EventOutbox pendingDispatched = save(EventStatus.PENDING, Instant.now());
    EventOutbox completedUndispatched = save(EventStatus.COMPLETED, null);
    EventOutbox completedDispatched = save(EventStatus.COMPLETED, Instant.now());
    EventOutbox failedUndispatched = save(EventStatus.FAILED, null);

    List<EventOutbox> result = eventOutboxRepository.findPending(Pageable.ofSize(10));

    assertThat(result).hasSize(1).containsExactly(pendingUndispatched);
    assertThat(result).doesNotContain(pendingDispatched);
    assertThat(result).doesNotContain(completedUndispatched);
    assertThat(result).doesNotContain(completedDispatched);
    assertThat(result).doesNotContain(failedUndispatched);
  }

  @Test
  void findPendingShouldReturnEmptyWhenNoPendingUndispatchedExist() {
    save(EventStatus.COMPLETED, null);
    save(EventStatus.FAILED, Instant.now());
    save(EventStatus.PENDING, Instant.now());

    assertThat(eventOutboxRepository.findPending(Pageable.ofSize(10))).isEmpty();
  }

  @Test
  void existsByIdempotencyKeyShouldWork() {
    String key = UUID.randomUUID().toString();
    save(EventStatus.PENDING, null, key);

    assertThat(eventOutboxRepository.existsByIdempotencyKey(key)).isTrue();
    assertThat(eventOutboxRepository.existsByIdempotencyKey("non-existent")).isFalse();
  }

  @Test
  void findPendingShouldRespectPageableLimit() {
    save(EventStatus.PENDING, null);
    save(EventStatus.PENDING, null);
    save(EventStatus.PENDING, null);

    List<EventOutbox> firstPage = eventOutboxRepository.findPending(PageRequest.of(0, 2));
    List<EventOutbox> secondPage = eventOutboxRepository.findPending(PageRequest.of(1, 2));

    assertThat(firstPage).hasSize(2);
    assertThat(secondPage).hasSize(1);
  }

  @Test
  void findPendingShouldOrderByCreatedAtAscending() throws Exception {
    EventOutbox first = save(EventStatus.PENDING, null);
    Thread.sleep(10);
    EventOutbox second = save(EventStatus.PENDING, null);
    Thread.sleep(10);
    EventOutbox third = save(EventStatus.PENDING, null);

    List<EventOutbox> result = eventOutboxRepository.findPending(Pageable.ofSize(10));

    assertThat(result).containsExactly(first, second, third);
  }
}
