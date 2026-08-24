package com.chrima.notification.dlq.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.dlq.model.DeadLetterNotification;
import com.chrima.notification.dlq.model.enums.DeadLetterStatus;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
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
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class DeadLetterNotificationRepositoryTest {

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

  @Autowired private DeadLetterNotificationRepository deadLetterNotificationRepository;

  @AfterEach
  void tearDown() {
    deadLetterNotificationRepository.deleteAll();
  }

  private DeadLetterNotification save(
      DeadLetterStatus status, Instant nextAttemptAt, String idempotencyKey) {
    return deadLetterNotificationRepository.save(
        DeadLetterNotification.builder()
            .notificationId(UUID.randomUUID())
            .recipient("user@example.com")
            .channel(ChannelType.EMAIL)
            .content("{\"subject\":\"Subject\",\"body\":\"Body\"}")
            .idempotencyKey(idempotencyKey)
            .failureReason("SES failure")
            .status(status)
            .attempts(0)
            .nextAttemptAt(nextAttemptAt)
            .build());
  }

  private DeadLetterNotification save(DeadLetterStatus status, Instant nextAttemptAt) {
    return save(status, nextAttemptAt, UUID.randomUUID().toString());
  }

  @Test
  void findReadyShouldReturnOnlyPendingWithNextAttemptAtInPast() {
    Instant now = Instant.now();
    Instant past = now.minus(10, ChronoUnit.SECONDS);
    Instant future = now.plus(60, ChronoUnit.SECONDS);

    DeadLetterNotification ready = save(DeadLetterStatus.PENDING, past);
    DeadLetterNotification notReadyFuture = save(DeadLetterStatus.PENDING, future);
    DeadLetterNotification completed = save(DeadLetterStatus.COMPLETED, past);
    DeadLetterNotification failed = save(DeadLetterStatus.FAILED, past);

    List<DeadLetterNotification> result =
        deadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).hasSize(1).containsExactly(ready);
    assertThat(result).doesNotContain(notReadyFuture, completed, failed);
  }

  @Test
  void findReadyShouldReturnEmptyWhenNoPendingReadyExist() {
    Instant now = Instant.now();
    save(DeadLetterStatus.PENDING, now.plus(60, ChronoUnit.SECONDS));
    save(DeadLetterStatus.COMPLETED, now.minus(10, ChronoUnit.SECONDS));
    save(DeadLetterStatus.FAILED, now.minus(10, ChronoUnit.SECONDS));

    List<DeadLetterNotification> result =
        deadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findReadyShouldReturnEmptyWhenTableIsEmpty() {
    List<DeadLetterNotification> result =
        deadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findReadyShouldRespectPageableLimit() {
    Instant past = Instant.now().minus(10, ChronoUnit.SECONDS);
    save(DeadLetterStatus.PENDING, past);
    save(DeadLetterStatus.PENDING, past);
    save(DeadLetterStatus.PENDING, past);

    List<DeadLetterNotification> firstPage =
        deadLetterNotificationRepository.findReady(Instant.now(), PageRequest.of(0, 2));
    List<DeadLetterNotification> secondPage =
        deadLetterNotificationRepository.findReady(Instant.now(), PageRequest.of(1, 2));

    assertThat(firstPage).hasSize(2);
    assertThat(secondPage).hasSize(1);
  }

  @Test
  void findReadyShouldOrderByNextAttemptAtAscending() throws Exception {
    Instant now = Instant.now();
    DeadLetterNotification first =
        save(DeadLetterStatus.PENDING, now.minus(30, ChronoUnit.SECONDS));
    Thread.sleep(5);
    DeadLetterNotification second =
        save(DeadLetterStatus.PENDING, now.minus(20, ChronoUnit.SECONDS));
    Thread.sleep(5);
    DeadLetterNotification third =
        save(DeadLetterStatus.PENDING, now.minus(10, ChronoUnit.SECONDS));

    List<DeadLetterNotification> result =
        deadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).containsExactly(first, second, third);
  }

  @Test
  void findReadyShouldExcludePendingWhenNextAttemptAtIsInFuture() {
    DeadLetterNotification future =
        save(DeadLetterStatus.PENDING, Instant.now().plus(60, ChronoUnit.SECONDS));

    List<DeadLetterNotification> result =
        deadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10));

    assertThat(result).doesNotContain(future).isEmpty();
  }

  @Test
  void findReadyShouldIncludePendingWhenNextAttemptAtEqualsNow() {
    Instant now = Instant.now();
    DeadLetterNotification exactlyNow = save(DeadLetterStatus.PENDING, now);

    List<DeadLetterNotification> result =
        deadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).hasSize(1).containsExactly(exactlyNow);
  }
}
