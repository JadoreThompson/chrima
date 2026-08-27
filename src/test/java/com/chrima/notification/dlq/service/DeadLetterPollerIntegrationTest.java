package com.chrima.notification.dlq.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.EmailNotificationContent;
import com.chrima.notification.channel.EmailNotificationChannel;
import com.chrima.notification.dlq.config.DeadLetterPollingProperties;
import com.chrima.notification.dlq.model.DeadLetterNotification;
import com.chrima.notification.dlq.model.enums.DeadLetterStatus;
import com.chrima.notification.dlq.repository.DeadLetterNotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
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
@Import({
  DeadLetterPoller.class,
  DeadLetterPollingProperties.class,
  ObjectMapper.class,
  EmailNotificationChannel.class
})
@Testcontainers
class DeadLetterPollerIntegrationTest {

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
    registry.add("notification.dlq.initial-delay", () -> "1s");
    registry.add("notification.dlq.backoff-multiplier", () -> "2.0");
    registry.add("notification.dlq.max-attempts", () -> "3");
  }

  @Autowired private DeadLetterNotificationRepository deadLetterNotificationRepository;

  @Autowired private DeadLetterPoller deadLetterPoller;

  @Autowired private DeadLetterPollingProperties deadLetterPollingProperties;

  @Autowired private ObjectMapper objectMapper;

  @MockitoBean private EmailNotificationChannel emailChannel;

  @BeforeEach
  void setUp() {
    when(emailChannel.supports(any())).thenAnswer(inv -> inv.getArgument(0) == ChannelType.EMAIL);
  }

  @AfterEach
  void tearDown() {
    deadLetterNotificationRepository.deleteAll();
  }

  private DeadLetterNotification createDlqEntry(
      int attempts, DeadLetterStatus status, Instant nextAttemptAt) throws Exception {
    EmailNotificationContent content = new EmailNotificationContent("Subject", "Body");
    return deadLetterNotificationRepository.save(
        DeadLetterNotification.builder()
            .notificationId(UUID.randomUUID())
            .recipient("user@example.com")
            .channel(ChannelType.EMAIL)
            .content(objectMapper.writeValueAsString(content))
            .idempotencyKey(UUID.randomUUID().toString())
            .failureReason("original failure")
            .attempts(attempts)
            .status(status)
            .nextAttemptAt(nextAttemptAt)
            .build());
  }

  private DeadLetterNotification createReadyDlqEntry(int attempts) throws Exception {
    return createDlqEntry(attempts, DeadLetterStatus.PENDING, Instant.now().minusSeconds(5));
  }

  @Test
  void shouldDeliverSuccessfullyAndMarkCompleted() throws Exception {
    DeadLetterNotification entry = createReadyDlqEntry(0);

    deadLetterPoller.run();

    verify(emailChannel).dispatch(eq("user@example.com"), any(EmailNotificationContent.class));

    DeadLetterNotification reloaded =
        deadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(DeadLetterStatus.COMPLETED);
    assertThat(reloaded.getDispatchedAt()).isNotNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(deadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10)))
        .isEmpty();
  }

  @Test
  void shouldIncrementAttemptsAndScheduleNextAttemptWithExponentialBackoffOnFailure()
      throws Exception {
    doThrow(new RuntimeException("SES failure"))
        .when(emailChannel)
        .dispatch(any(), any(EmailNotificationContent.class));

    DeadLetterNotification entry = createReadyDlqEntry(0);
    Instant before = Instant.now();

    deadLetterPoller.run();

    DeadLetterNotification reloaded =
        deadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(DeadLetterStatus.PENDING);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(reloaded.getNextAttemptAt()).isNotNull();
    // initial delay 1s, multiplier 2.0, attempts=1 => delay 1s
    long delay = Duration.between(before, reloaded.getNextAttemptAt()).toMillis();
    assertThat(delay).isGreaterThanOrEqualTo(900);
    assertThat(delay).isLessThanOrEqualTo(1500);
    // should not be ready immediately after backoff scheduling (nextAttempt in future)
    assertThat(deadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10)))
        .isEmpty();
    // but should be ready after ~1s
    assertThat(
            deadLetterNotificationRepository.findReady(
                Instant.now().plusSeconds(2), Pageable.ofSize(10)))
        .hasSize(1);
  }

  @Test
  void shouldApplyExponentialBackoffMultiplierOnSecondFailure() throws Exception {
    doThrow(new RuntimeException("SES failure"))
        .when(emailChannel)
        .dispatch(any(), any(EmailNotificationContent.class));

    // simulate entry that already failed once with nextAttempt in past
    DeadLetterNotification entry = createReadyDlqEntry(1);

    Instant before = Instant.now();
    deadLetterPoller.run();

    DeadLetterNotification reloaded =
        deadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(2);
    assertThat(reloaded.getStatus()).isEqualTo(DeadLetterStatus.PENDING);
    // attempts=2 => delay 2s (1s * 2^(2-1))
    long delay = Duration.between(before, reloaded.getNextAttemptAt()).toMillis();
    assertThat(delay).isGreaterThanOrEqualTo(1900);
    assertThat(delay).isLessThanOrEqualTo(2500);
  }

  @Test
  void shouldApplyExponentialBackoffOnThirdAttempt() throws Exception {
    // use poller directly to verify calculation
    Instant now = Instant.now();
    Instant next1 = deadLetterPoller.calculateNextAttempt(1, now);
    Instant next2 = deadLetterPoller.calculateNextAttempt(2, now);
    Instant next3 = deadLetterPoller.calculateNextAttempt(3, now);

    assertThat(Duration.between(now, next1).toMillis()).isEqualTo(1000);
    assertThat(Duration.between(now, next2).toMillis()).isEqualTo(2000);
    assertThat(Duration.between(now, next3).toMillis()).isEqualTo(4000);
  }

  @Test
  void shouldFailWhenMaxAttemptsBreached() throws Exception {
    doThrow(new RuntimeException("SES failure"))
        .when(emailChannel)
        .dispatch(any(), any(EmailNotificationContent.class));

    // maxAttempts is 3, entry already has 2 attempts, next failure should mark FAILED
    DeadLetterNotification entry = createReadyDlqEntry(2);

    deadLetterPoller.run();

    DeadLetterNotification reloaded =
        deadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(3);
    assertThat(reloaded.getStatus()).isEqualTo(DeadLetterStatus.FAILED);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(deadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10)))
        .isEmpty();
    assertThat(
            deadLetterNotificationRepository.findReady(
                Instant.now().plusSeconds(10), Pageable.ofSize(10)))
        .isEmpty();
  }

  @Test
  void shouldNotProcessWhenNextAttemptIsInFuture() throws Exception {
    createDlqEntry(0, DeadLetterStatus.PENDING, Instant.now().plusSeconds(60));

    deadLetterPoller.run();

    // verify dispatch was not called
    verify(emailChannel, org.mockito.Mockito.never())
        .dispatch(any(), any(EmailNotificationContent.class));
    assertThat(deadLetterNotificationRepository.findAll()).hasSize(1);
  }

  @Test
  void shouldNotProcessCompletedOrFailedEntries() throws Exception {
    createDlqEntry(0, DeadLetterStatus.COMPLETED, Instant.now().minusSeconds(5));
    createDlqEntry(0, DeadLetterStatus.FAILED, Instant.now().minusSeconds(5));

    deadLetterPoller.run();

    verify(emailChannel, org.mockito.Mockito.never())
        .dispatch(any(), any(EmailNotificationContent.class));
  }

  @Test
  void shouldRespectConfigurableInitialDelayAndMaxAttempts() {
    assertThat(deadLetterPollingProperties.getInitialDelay()).isEqualTo(Duration.ofSeconds(1));
    assertThat(deadLetterPollingProperties.getMaxAttempts()).isEqualTo(3);
    assertThat(deadLetterPollingProperties.getBackoffMultiplier()).isEqualTo(2.0);
  }
}
