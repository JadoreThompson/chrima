package com.chrima.notification.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.model.Notification;
import com.chrima.notification.model.enums.NotificationStatus;
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
class NotificationRepositoryTest {

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

  @Autowired private NotificationRepository notificationRepository;

  @AfterEach
  void tearDown() {
    notificationRepository.deleteAll();
  }

  private Notification saveNotification(
      NotificationStatus status, Instant dispatchedAt, String idempotencyKey) {
    Notification notification = new Notification();
    notification.setRecipient("user@example.com");
    notification.setChannel(ChannelType.EMAIL);
    notification.setContent("{\"subject\":\"Subject\",\"body\":\"Body\"}");
    notification.setStatus(status);
    notification.setIdempotencyKey(idempotencyKey);
    notification.setDispatchedAt(dispatchedAt);
    return notificationRepository.save(notification);
  }

  private Notification saveNotification(NotificationStatus status, Instant dispatchedAt) {
    return saveNotification(status, dispatchedAt, UUID.randomUUID().toString());
  }

  @Test
  void findPendingShouldReturnOnlyPendingWithNullDispatchedAt() {
    Notification pendingUndispatched = saveNotification(NotificationStatus.PENDING, null);
    Notification pendingDispatched = saveNotification(NotificationStatus.PENDING, Instant.now());
    Notification completedUndispatched = saveNotification(NotificationStatus.COMPLETED, null);
    Notification completedDispatched =
        saveNotification(NotificationStatus.COMPLETED, Instant.now());
    Notification failedUndispatched = saveNotification(NotificationStatus.FAILED, null);
    Notification failedDispatched = saveNotification(NotificationStatus.FAILED, Instant.now());

    List<Notification> result = notificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result)
        .hasSize(1)
        .containsExactly(pendingUndispatched)
        .doesNotContain(pendingDispatched)
        .doesNotContain(completedUndispatched)
        .doesNotContain(completedDispatched)
        .doesNotContain(failedUndispatched)
        .doesNotContain(failedDispatched);

    // all returned entries must satisfy pending + null dispatchedAt
    assertThat(result)
        .allSatisfy(
            n -> {
              assertThat(n.getStatus()).isEqualTo(NotificationStatus.PENDING);
              assertThat(n.getDispatchedAt()).isNull();
            });
  }

  @Test
  void findPendingShouldReturnEmptyWhenNoPendingUndispatchedExist() {
    saveNotification(NotificationStatus.COMPLETED, null);
    saveNotification(NotificationStatus.FAILED, Instant.now());
    saveNotification(NotificationStatus.PENDING, Instant.now());

    List<Notification> result = notificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findPendingShouldReturnEmptyWhenTableIsEmpty() {
    List<Notification> result = notificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findPendingShouldReturnMultiplePendingUndispatched() {
    Notification first = saveNotification(NotificationStatus.PENDING, null);
    Notification second = saveNotification(NotificationStatus.PENDING, null);
    saveNotification(NotificationStatus.FAILED, null);
    saveNotification(NotificationStatus.COMPLETED, Instant.now());

    List<Notification> result = notificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).hasSize(2).containsExactlyInAnyOrder(first, second);
  }

  @Test
  void findPendingShouldRespectPageableLimit() {
    saveNotification(NotificationStatus.PENDING, null);
    saveNotification(NotificationStatus.PENDING, null);
    saveNotification(NotificationStatus.PENDING, null);

    List<Notification> firstPage = notificationRepository.findPending(PageRequest.of(0, 2));
    List<Notification> secondPage = notificationRepository.findPending(PageRequest.of(1, 2));

    assertThat(firstPage).hasSize(2);
    assertThat(secondPage).hasSize(1);
  }

  @Test
  void findPendingShouldOrderByCreatedAtAscending() throws Exception {
    Notification first = saveNotification(NotificationStatus.PENDING, null);
    // ensure distinct createdAt timestamps (CreationTimestamp precision is milliseconds)
    Thread.sleep(10);
    Notification second = saveNotification(NotificationStatus.PENDING, null);
    Thread.sleep(10);
    Notification third = saveNotification(NotificationStatus.PENDING, null);

    List<Notification> result = notificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).containsExactly(first, second, third);
  }

  @Test
  void findPendingShouldExcludeCompletedEvenWhenDispatchedAtIsNull() {
    saveNotification(NotificationStatus.COMPLETED, null);

    List<Notification> result = notificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findPendingShouldExcludePendingWhenDispatchedAtIsNotNull() {
    Notification dispatchedPending = saveNotification(NotificationStatus.PENDING, Instant.now());

    List<Notification> result = notificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).doesNotContain(dispatchedPending).isEmpty();
  }
}
