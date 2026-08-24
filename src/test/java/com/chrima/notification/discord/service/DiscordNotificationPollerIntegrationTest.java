package com.chrima.notification.discord.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.channel.DiscordNotificationChannel;
import com.chrima.notification.discord.dlq.model.DiscordDeadLetterNotification;
import com.chrima.notification.discord.dlq.model.enums.DiscordDeadLetterStatus;
import com.chrima.notification.discord.dlq.repository.DiscordDeadLetterNotificationRepository;
import com.chrima.notification.discord.model.DiscordNotification;
import com.chrima.notification.discord.model.DiscordNotificationContentRegistry;
import com.chrima.notification.discord.model.enums.DiscordNotificationStatus;
import com.chrima.notification.discord.repository.DiscordNotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.List;
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
class DiscordNotificationPollerIntegrationTest {

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
    registry.add("discord.dlq.max-attempts", () -> "5");
    registry.add("discord.dlq.batch-size", () -> "10");
    registry.add("discord.dlq.polling-delay", () -> "1000000");
    registry.add("discord.dlq.initial-delay", () -> "1s");
    registry.add("discord.dlq.backoff-multiplier", () -> "2.0");
    registry.add("notification.polling.max-attempts", () -> "3");
    registry.add("notification.polling.batch-size", () -> "10");
    registry.add("notification.polling.delay", () -> "1000000");
    registry.add("notification.dlq.max-attempts", () -> "5");
    registry.add("notification.dlq.batch-size", () -> "10");
    registry.add("notification.dlq.polling-delay", () -> "1000000");
    registry.add("notification.dlq.initial-delay", () -> "1s");
  }

  @Autowired private DiscordNotificationRepository discordNotificationRepository;

  @Autowired
  private DiscordDeadLetterNotificationRepository discordDeadLetterNotificationRepository;

  @Autowired private DiscordNotificationPoller discordNotificationPoller;

  @Autowired private ObjectMapper objectMapper;

  @MockitoBean private DiscordNotificationChannel discordNotificationChannel;

  @MockitoBean private DiscordNotificationContentRegistry discordNotificationContentRegistry;

  @BeforeEach
  void setUp() throws Exception {
    doReturn(TestDiscordContent.class).when(discordNotificationContentRegistry).get("TEST_TYPE");
    when(discordNotificationChannel.send(any(), any(), any(), any())).thenReturn(123456789L);
  }

  @AfterEach
  void tearDown() {
    discordDeadLetterNotificationRepository.deleteAll();
    discordNotificationRepository.deleteAll();
  }

  private DiscordNotification createPendingNotification(int attempts) {
    return discordNotificationRepository.save(
        DiscordNotification.builder()
            .guildId(12345L)
            .channelId(67890L)
            .type("TEST_TYPE")
            .content("{\"key\":\"value\"}")
            .idempotencyKey(UUID.randomUUID().toString())
            .attempts(attempts)
            .status(DiscordNotificationStatus.PENDING)
            .build());
  }

  @Test
  void shouldDeliverSuccessfullyAndMarkCompleted() {
    DiscordNotification notification = createPendingNotification(0);

    discordNotificationPoller.run();

    verify(discordNotificationChannel)
        .send(eq(12345L), eq(67890L), any(IDiscordNotificationContent.class), any());

    DiscordNotification reloaded =
        discordNotificationRepository.findById(notification.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(DiscordNotificationStatus.COMPLETED);
    assertThat(reloaded.getDispatchedAt()).isNotNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(reloaded.getDiscordMessageId()).isEqualTo(123456789L);
    assertThat(discordNotificationRepository.findPending(Pageable.ofSize(10))).isEmpty();
  }

  @Test
  void shouldIncrementAttemptsOnFailureAndRemainPending() {
    doThrow(new RuntimeException("Discord failure"))
        .when(discordNotificationChannel)
        .send(any(), any(), any(), any());

    DiscordNotification notification = createPendingNotification(0);

    discordNotificationPoller.run();

    DiscordNotification reloaded =
        discordNotificationRepository.findById(notification.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(DiscordNotificationStatus.PENDING);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(discordNotificationRepository.findPending(Pageable.ofSize(10))).hasSize(1);
    assertThat(discordDeadLetterNotificationRepository.findAll()).isEmpty();
  }

  @Test
  void shouldAbandonNotificationWhenMaxAttemptsBreachedAndMarkFailed() {
    doThrow(new RuntimeException("Discord failure"))
        .when(discordNotificationChannel)
        .send(any(), any(), any(), any());

    DiscordNotification notification = createPendingNotification(2);

    discordNotificationPoller.run();

    DiscordNotification reloaded =
        discordNotificationRepository.findById(notification.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(3);
    assertThat(reloaded.getStatus()).isEqualTo(DiscordNotificationStatus.FAILED);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(discordNotificationRepository.findPending(Pageable.ofSize(10))).isEmpty();

    List<DiscordDeadLetterNotification> dlqEntries =
        discordDeadLetterNotificationRepository.findAll();
    assertThat(dlqEntries).hasSize(1);
    DiscordDeadLetterNotification dlq = dlqEntries.get(0);
    assertThat(dlq.getDiscordNotificationId()).isEqualTo(notification.getId());
    assertThat(dlq.getGuildId()).isEqualTo(notification.getGuildId());
    assertThat(dlq.getChannelId()).isEqualTo(notification.getChannelId());
    assertThat(dlq.getType()).isEqualTo(notification.getType());
    assertThat(dlq.getContent()).isEqualTo(notification.getContent());
    assertThat(dlq.getIdempotencyKey()).isEqualTo(notification.getIdempotencyKey());
    assertThat(dlq.getStatus()).isEqualTo(DiscordDeadLetterStatus.PENDING);
    assertThat(dlq.getAttempts()).isEqualTo(0);
    assertThat(dlq.getNextAttemptAt()).isNotNull();
    assertThat(dlq.getFailureReason()).contains("Discord failure");
  }

  @Test
  void shouldMoveFailedNotificationToDlqWithExponentialBackoffDelay() {
    doThrow(new RuntimeException("Discord failure"))
        .when(discordNotificationChannel)
        .send(any(), any(), any(), any());

    DiscordNotification notification = createPendingNotification(2);

    long before = System.currentTimeMillis();
    discordNotificationPoller.run();
    long after = System.currentTimeMillis();

    DiscordDeadLetterNotification dlq = discordDeadLetterNotificationRepository.findAll().get(0);
    assertThat(dlq.getNextAttemptAt()).isNotNull();
    assertThat(dlq.getNextAttemptAt().toEpochMilli()).isGreaterThanOrEqualTo(before + 900);
    assertThat(dlq.getNextAttemptAt().toEpochMilli()).isLessThanOrEqualTo(after + 1500);
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
