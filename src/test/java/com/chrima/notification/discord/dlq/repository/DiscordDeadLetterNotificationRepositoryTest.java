package com.chrima.notification.discord.dlq.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.notification.discord.dlq.model.DiscordDeadLetterNotification;
import com.chrima.notification.discord.dlq.model.enums.DiscordDeadLetterStatus;
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
class DiscordDeadLetterNotificationRepositoryTest {

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

  @Autowired
  private DiscordDeadLetterNotificationRepository discordDeadLetterNotificationRepository;

  @AfterEach
  void tearDown() {
    discordDeadLetterNotificationRepository.deleteAll();
  }

  private DiscordDeadLetterNotification save(
      DiscordDeadLetterStatus status, Instant nextAttemptAt, String idempotencyKey) {
    return discordDeadLetterNotificationRepository.save(
        DiscordDeadLetterNotification.builder()
            .discordNotificationId(UUID.randomUUID())
            .guildId(12345L)
            .channelId(67890L)
            .type("TEST_TYPE")
            .content("{\"key\":\"value\"}")
            .idempotencyKey(idempotencyKey)
            .failureReason("Discord failure")
            .status(status)
            .attempts(0)
            .nextAttemptAt(nextAttemptAt)
            .build());
  }

  private DiscordDeadLetterNotification save(
      DiscordDeadLetterStatus status, Instant nextAttemptAt) {
    return save(status, nextAttemptAt, UUID.randomUUID().toString());
  }

  @Test
  void findReadyShouldReturnOnlyPendingWithNextAttemptAtInPast() {
    Instant now = Instant.now();
    Instant past = now.minus(10, ChronoUnit.SECONDS);
    Instant future = now.plus(60, ChronoUnit.SECONDS);

    DiscordDeadLetterNotification ready = save(DiscordDeadLetterStatus.PENDING, past);
    DiscordDeadLetterNotification notReadyFuture = save(DiscordDeadLetterStatus.PENDING, future);
    DiscordDeadLetterNotification completed = save(DiscordDeadLetterStatus.COMPLETED, past);
    DiscordDeadLetterNotification failed = save(DiscordDeadLetterStatus.FAILED, past);

    List<DiscordDeadLetterNotification> result =
        discordDeadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).hasSize(1).containsExactly(ready);
    assertThat(result).doesNotContain(notReadyFuture, completed, failed);
  }

  @Test
  void findReadyShouldReturnEmptyWhenNoPendingReadyExist() {
    Instant now = Instant.now();
    save(DiscordDeadLetterStatus.PENDING, now.plus(60, ChronoUnit.SECONDS));
    save(DiscordDeadLetterStatus.COMPLETED, now.minus(10, ChronoUnit.SECONDS));
    save(DiscordDeadLetterStatus.FAILED, now.minus(10, ChronoUnit.SECONDS));

    List<DiscordDeadLetterNotification> result =
        discordDeadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findReadyShouldReturnEmptyWhenTableIsEmpty() {
    List<DiscordDeadLetterNotification> result =
        discordDeadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findReadyShouldRespectPageableLimit() {
    Instant past = Instant.now().minus(10, ChronoUnit.SECONDS);
    save(DiscordDeadLetterStatus.PENDING, past);
    save(DiscordDeadLetterStatus.PENDING, past);
    save(DiscordDeadLetterStatus.PENDING, past);

    List<DiscordDeadLetterNotification> firstPage =
        discordDeadLetterNotificationRepository.findReady(Instant.now(), PageRequest.of(0, 2));
    List<DiscordDeadLetterNotification> secondPage =
        discordDeadLetterNotificationRepository.findReady(Instant.now(), PageRequest.of(1, 2));

    assertThat(firstPage).hasSize(2);
    assertThat(secondPage).hasSize(1);
  }

  @Test
  void findReadyShouldOrderByNextAttemptAtAscending() throws Exception {
    Instant now = Instant.now();
    DiscordDeadLetterNotification first =
        save(DiscordDeadLetterStatus.PENDING, now.minus(30, ChronoUnit.SECONDS));
    Thread.sleep(5);
    DiscordDeadLetterNotification second =
        save(DiscordDeadLetterStatus.PENDING, now.minus(20, ChronoUnit.SECONDS));
    Thread.sleep(5);
    DiscordDeadLetterNotification third =
        save(DiscordDeadLetterStatus.PENDING, now.minus(10, ChronoUnit.SECONDS));

    List<DiscordDeadLetterNotification> result =
        discordDeadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).containsExactly(first, second, third);
  }

  @Test
  void findReadyShouldExcludePendingWhenNextAttemptAtIsInFuture() {
    DiscordDeadLetterNotification future =
        save(DiscordDeadLetterStatus.PENDING, Instant.now().plus(60, ChronoUnit.SECONDS));

    List<DiscordDeadLetterNotification> result =
        discordDeadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10));

    assertThat(result).doesNotContain(future).isEmpty();
  }

  @Test
  void findReadyShouldIncludePendingWhenNextAttemptAtEqualsNow() {
    Instant now = Instant.now();
    DiscordDeadLetterNotification exactlyNow = save(DiscordDeadLetterStatus.PENDING, now);

    List<DiscordDeadLetterNotification> result =
        discordDeadLetterNotificationRepository.findReady(now, Pageable.ofSize(10));

    assertThat(result).hasSize(1).containsExactly(exactlyNow);
  }
}
