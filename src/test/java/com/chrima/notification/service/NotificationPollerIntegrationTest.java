package com.chrima.notification.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.EmailNotificationContent;
import com.chrima.notification.channel.EmailNotificationChannel;
import com.chrima.notification.dlq.model.DeadLetterNotification;
import com.chrima.notification.dlq.model.enums.DeadLetterStatus;
import com.chrima.notification.dlq.repository.DeadLetterNotificationRepository;
import com.chrima.notification.model.Notification;
import com.chrima.notification.model.enums.NotificationStatus;
import com.chrima.notification.repository.NotificationRepository;
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
class NotificationPollerIntegrationTest {

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
    registry.add("notification.polling.max-attempts", () -> "3");
    registry.add("notification.polling.batch-size", () -> "10");
    registry.add("notification.polling.delay", () -> "1000000");
    registry.add("notification.dlq.max-attempts", () -> "5");
    registry.add("notification.dlq.batch-size", () -> "10");
    registry.add("notification.dlq.polling-delay", () -> "1000000");
    registry.add("notification.dlq.initial-delay", () -> "1s");
    registry.add("notification.dlq.backoff-multiplier", () -> "2.0");
  }

  @Autowired private NotificationRepository notificationRepository;

  @Autowired private DeadLetterNotificationRepository deadLetterNotificationRepository;

  @Autowired private NotificationPoller notificationPoller;

  @Autowired private ObjectMapper objectMapper;

  @MockitoBean private EmailNotificationChannel emailChannel;

  @BeforeEach
  void setUp() {
    when(emailChannel.supports(any())).thenAnswer(inv -> inv.getArgument(0) == ChannelType.EMAIL);
  }

  @AfterEach
  void tearDown() {
    deadLetterNotificationRepository.deleteAll();
    notificationRepository.deleteAll();
  }

  private Notification createPendingNotification(int attempts) throws Exception {
    EmailNotificationContent content = new EmailNotificationContent("Subject", "Body");
    Notification notification = new Notification();
    notification.setRecipient("user@example.com");
    notification.setChannel(ChannelType.EMAIL);
    notification.setContent(objectMapper.writeValueAsString(content));
    notification.setStatus(NotificationStatus.PENDING);
    notification.setAttempts(attempts);
    notification.setIdempotencyKey(UUID.randomUUID().toString());
    return notificationRepository.save(notification);

    //        return notificationRepository.save(
    //                Notification.builder()
    //                        .recipient("user@example.com")
    //                        .channel(ChannelType.EMAIL)
    //                        .content(objectMapper.writeValueAsString(content))
    //                        .idempotencyKey(UUID.randomUUID().toString())
    //                        .attempts(attempts)
    //                        .status(NotificationStatus.PENDING)
    //                        .build());
  }

  @Test
  void shouldDeliverSuccessfullyAndMarkCompleted() throws Exception {
    Notification notification = createPendingNotification(0);

    notificationPoller.run();

    verify(emailChannel).dispatch(eq("user@example.com"), any(EmailNotificationContent.class));

    Notification reloaded = notificationRepository.findById(notification.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(NotificationStatus.COMPLETED);
    assertThat(reloaded.getDispatchedAt()).isNotNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(notificationRepository.findPending(Pageable.ofSize(10))).isEmpty();
  }

  @Test
  void shouldIncrementAttemptsOnFailureAndRemainPending() throws Exception {
    doThrow(new RuntimeException("SES failure"))
        .when(emailChannel)
        .dispatch(any(), any(EmailNotificationContent.class));

    Notification notification = createPendingNotification(0);

    notificationPoller.run();
    System.out.println("Notification id=" + notification.getId());
    //        Thread.sleep(100000);

    Notification reloaded = notificationRepository.findById(notification.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(1);
    assertThat(reloaded.getStatus()).isEqualTo(NotificationStatus.PENDING);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(notificationRepository.findPending(Pageable.ofSize(10))).hasSize(1);
    assertThat(deadLetterNotificationRepository.findAll()).isEmpty();
  }

  @Test
  void shouldAbandonNotificationWhenMaxAttemptsBreachedAndMarkFailed() throws Exception {
    doThrow(new RuntimeException("SES failure"))
        .when(emailChannel)
        .dispatch(any(), any(EmailNotificationContent.class));

    Notification notification = createPendingNotification(2);

    notificationPoller.run();

    Notification reloaded = notificationRepository.findById(notification.getId()).orElseThrow();
    assertThat(reloaded.getAttempts()).isEqualTo(3);
    assertThat(reloaded.getStatus()).isEqualTo(NotificationStatus.FAILED);
    assertThat(reloaded.getDispatchedAt()).isNull();
    assertThat(reloaded.getLastAttemptedAt()).isNotNull();
    assertThat(notificationRepository.findPending(Pageable.ofSize(10))).isEmpty();

    List<DeadLetterNotification> dlqEntries = deadLetterNotificationRepository.findAll();
    assertThat(dlqEntries).hasSize(1);
    DeadLetterNotification dlq = dlqEntries.get(0);
    assertThat(dlq.getNotificationId()).isEqualTo(notification.getId());
    assertThat(dlq.getRecipient()).isEqualTo(notification.getRecipient());
    assertThat(dlq.getChannel()).isEqualTo(notification.getChannel());
    assertThat(dlq.getContent()).isEqualTo(notification.getContent());
    assertThat(dlq.getStatus()).isEqualTo(DeadLetterStatus.PENDING);
    assertThat(dlq.getAttempts()).isEqualTo(0);
    assertThat(dlq.getNextAttemptAt()).isNotNull();
    assertThat(dlq.getFailureReason()).contains("SES failure");
  }

  @Test
  void shouldMoveFailedNotificationToDlqWithExponentialBackoffDelay() throws Exception {
    doThrow(new RuntimeException("SES failure"))
        .when(emailChannel)
        .dispatch(any(), any(EmailNotificationContent.class));

    Notification notification = createPendingNotification(2);

    long before = System.currentTimeMillis();
    notificationPoller.run();
    long after = System.currentTimeMillis();

    DeadLetterNotification dlq = deadLetterNotificationRepository.findAll().get(0);
    assertThat(dlq.getNextAttemptAt()).isNotNull();
    // initial delay is 1s, so nextAttemptAt should be roughly before+1000
    assertThat(dlq.getNextAttemptAt().toEpochMilli()).isGreaterThanOrEqualTo(before + 900);
    assertThat(dlq.getNextAttemptAt().toEpochMilli()).isLessThanOrEqualTo(after + 1500);
  }
}
