package com.chrima.notification.discord.dlq.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.channel.DiscordNotificationChannel;
import com.chrima.notification.discord.dlq.config.DiscordDeadLetterProperties;
import com.chrima.notification.discord.dlq.model.DiscordDeadLetterNotification;
import com.chrima.notification.discord.dlq.model.enums.DiscordDeadLetterStatus;
import com.chrima.notification.discord.dlq.repository.DiscordDeadLetterNotificationRepository;
import com.chrima.notification.discord.model.DiscordNotificationContentRegistry;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.domain.Pageable;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@Testcontainers
class DiscordDeadLetterPollerIntegrationTest {

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
    registry.add("discord.token", () -> "test-token");
    registry.add("discord.polling.max-attempts", () -> "3");
    registry.add("discord.polling.batch-size", () -> "10");
    registry.add("discord.polling.fixed-delay", () -> "1000000");
    registry.add("discord.polling.initial-delay", () -> "1000000");
    registry.add("discord.polling.enabled", () -> "true");
    registry.add("discord.dlq.max-attempts", () -> "3");
    registry.add("discord.dlq.batch-size", () -> "10");
    registry.add("discord.dlq.polling-delay", () -> "1000000");
    registry.add("discord.dlq.initial-delay", () -> "1s");
    registry.add("discord.dlq.backoff-multiplier", () -> "2.0");
    registry.add("notification.polling.max-attempts", () -> "3");
    registry.add("notification.polling.batch-size", () -> "10");
    registry.add("notification.polling.delay", () -> "1000000");
  }

  @Autowired
  private DiscordDeadLetterNotificationRepository discordDeadLetterNotificationRepository;

  @Autowired private DiscordDeadLetterPoller discordDeadLetterPoller;

  @Autowired private DiscordDeadLetterProperties discordDeadLetterProperties;

  @Autowired private ObjectMapper objectMapper;

  @MockitoBean private DiscordNotificationChannel discordNotificationChannel;

  @MockitoBean private DiscordNotificationContentRegistry discordNotificationContentRegistry;

  @BeforeEach
  void setUp() throws Exception {
    doReturn(TestDiscordContent.class).when(discordNotificationContentRegistry).get("TEST_TYPE");
    when(discordNotificationChannel.send(any(), any(), any(), any())).thenReturn(987654321L);
  }

  @AfterEach
  void tearDown() {
    discordDeadLetterNotificationRepository.deleteAll();
  }

  private DiscordDeadLetterNotification createDlqEntry(
      int attempts, DiscordDeadLetterStatus status, Instant nextAttemptAt) {
    return discordDeadLetterNotificationRepository.save(
        DiscordDeadLetterNotification.builder()
            .discordNotificationId(UUID.randomUUID())
            .guildId(12345L)
            .channelId(67890L)
            .type("TEST_TYPE")
            .content("{\"key\":\"value\"}")
            .idempotencyKey(UUID.randomUUID().toString())
            .failureReason("original failure")
            .attempts(attempts)
            .status(status)
            .nextAttemptAt(nextAttemptAt)
            .build());
  }

  private DiscordDeadLetterNotification createReadyDlqEntry(int attempts) {
    return createDlqEntry(attempts, DiscordDeadLetterStatus.PENDING, Instant.now().minusSeconds(5));
  }

  @Test
  void shouldDeliverSuccessfullyAndMarkCompleted() {
    DiscordDeadLetterNotification entry = createReadyDlqEntry(0);

    discordDeadLetterPoller.run();

    verify(discordNotificationChannel)
        .send(eq(12345L), eq(67890L), any(IDiscordNotificationContent.class), any());

    DiscordDeadLetterNotification reloaded =
        discordDeadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(DiscordDeadLetterStatus.COMPLETED);
    assertThat(reloaded.getDispatchedAt()).isNotNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(
            discordDeadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10)))
        .isEmpty();
  }

  @Test
  void shouldIncrementAttemptsAndScheduleNextAttemptWithExponentialBackoffOnFailure() {
    doThrow(new RuntimeException("Discord send failure"))
        .when(discordNotificationChannel)
        .send(any(), any(), any(), any());

    DiscordDeadLetterNotification entry = createReadyDlqEntry(0);
    Instant before = Instant.now();

    discordDeadLetterPoller.run();

    DiscordDeadLetterNotification reloaded =
        discordDeadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(DiscordDeadLetterStatus.PENDING);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(reloaded.getNextAttemptAt()).isNotNull();
    long delay = Duration.between(before, reloaded.getNextAttemptAt()).toMillis();
    assertThat(delay).isGreaterThanOrEqualTo(900);
    assertThat(delay).isLessThanOrEqualTo(1500);
    assertThat(
            discordDeadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10)))
        .isEmpty();
    assertThat(
            discordDeadLetterNotificationRepository.findReady(
                Instant.now().plusSeconds(2), Pageable.ofSize(10)))
        .hasSize(1);
  }

  @Test
  void shouldApplyExponentialBackoffMultiplierOnSecondFailure() {
    doThrow(new RuntimeException("Discord send failure"))
        .when(discordNotificationChannel)
        .send(any(), any(), any(), any());

    DiscordDeadLetterNotification entry = createReadyDlqEntry(1);

    Instant before = Instant.now();
    discordDeadLetterPoller.run();

    DiscordDeadLetterNotification reloaded =
        discordDeadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(2);
    assertThat(reloaded.getStatus()).isEqualTo(DiscordDeadLetterStatus.PENDING);
    long delay = Duration.between(before, reloaded.getNextAttemptAt()).toMillis();
    assertThat(delay).isGreaterThanOrEqualTo(1900);
    assertThat(delay).isLessThanOrEqualTo(2500);
  }

  @Test
  void shouldApplyExponentialBackoffOnThirdAttempt() {
    Instant now = Instant.now();
    Instant next1 = discordDeadLetterPoller.calculateNextAttempt(1, now);
    Instant next2 = discordDeadLetterPoller.calculateNextAttempt(2, now);
    Instant next3 = discordDeadLetterPoller.calculateNextAttempt(3, now);

    assertThat(Duration.between(now, next1).toMillis()).isEqualTo(1000);
    assertThat(Duration.between(now, next2).toMillis()).isEqualTo(2000);
    assertThat(Duration.between(now, next3).toMillis()).isEqualTo(4000);
  }

  @Test
  void shouldFailWhenMaxAttemptsBreached() {
    doThrow(new RuntimeException("Discord send failure"))
        .when(discordNotificationChannel)
        .send(any(), any(), any(), any());

    DiscordDeadLetterNotification entry = createReadyDlqEntry(2);

    discordDeadLetterPoller.run();

    DiscordDeadLetterNotification reloaded =
        discordDeadLetterNotificationRepository.findById(entry.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(3);
    assertThat(reloaded.getStatus()).isEqualTo(DiscordDeadLetterStatus.FAILED);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(
            discordDeadLetterNotificationRepository.findReady(Instant.now(), Pageable.ofSize(10)))
        .isEmpty();
    assertThat(
            discordDeadLetterNotificationRepository.findReady(
                Instant.now().plusSeconds(10), Pageable.ofSize(10)))
        .isEmpty();
  }

  @Test
  void shouldNotProcessWhenNextAttemptIsInFuture() {
    createDlqEntry(0, DiscordDeadLetterStatus.PENDING, Instant.now().plusSeconds(60));

    discordDeadLetterPoller.run();

    verify(discordNotificationChannel, org.mockito.Mockito.never())
        .send(any(), any(), any(), any());
    assertThat(discordDeadLetterNotificationRepository.findAll()).hasSize(1);
  }

  @Test
  void shouldNotProcessCompletedOrFailedEntries() {
    createDlqEntry(0, DiscordDeadLetterStatus.COMPLETED, Instant.now().minusSeconds(5));
    createDlqEntry(0, DiscordDeadLetterStatus.FAILED, Instant.now().minusSeconds(5));

    discordDeadLetterPoller.run();

    verify(discordNotificationChannel, org.mockito.Mockito.never())
        .send(any(), any(), any(), any());
  }

  @Test
  void shouldRespectConfigurableInitialDelayAndMaxAttempts() {
    assertThat(discordDeadLetterProperties.getInitialDelay()).isEqualTo(Duration.ofSeconds(1));
    assertThat(discordDeadLetterProperties.getMaxAttempts()).isEqualTo(3);
    assertThat(discordDeadLetterProperties.getBackoffMultiplier()).isEqualTo(2.0);
  }

  static class TestDiscordContent implements IDiscordNotificationContent {
    private String key = "value";

    @Override
    public String subject() {
      return "Test Subject";
    }

    @Override
    public String body() {
      return "Test Body";
    }
  }
}
