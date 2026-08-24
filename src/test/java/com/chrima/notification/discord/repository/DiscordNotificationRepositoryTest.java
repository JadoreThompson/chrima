package com.chrima.notification.discord.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.notification.discord.model.DiscordNotification;
import com.chrima.notification.discord.model.enums.DiscordNotificationStatus;
import java.time.Instant;
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
class DiscordNotificationRepositoryTest {

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

  @Autowired private DiscordNotificationRepository discordNotificationRepository;

  @AfterEach
  void tearDown() {
    discordNotificationRepository.deleteAll();
  }

  private DiscordNotification saveNotification(
      DiscordNotificationStatus status, Instant dispatchedAt, String idempotencyKey) {
    return discordNotificationRepository.save(
        DiscordNotification.builder()
            .guildId(12345L)
            .channelId(67890L)
            .type("TEST_TYPE")
            .content("{\"key\":\"value\"}")
            .idempotencyKey(idempotencyKey)
            .status(status)
            .dispatchedAt(dispatchedAt)
            .build());
  }

  private DiscordNotification saveNotification(
      DiscordNotificationStatus status, Instant dispatchedAt) {
    return saveNotification(status, dispatchedAt, UUID.randomUUID().toString());
  }

  @Test
  void findPendingShouldReturnOnlyPendingWithNullDispatchedAt() {
    DiscordNotification pendingUndispatched =
        saveNotification(DiscordNotificationStatus.PENDING, null);
    DiscordNotification pendingDispatched =
        saveNotification(DiscordNotificationStatus.PENDING, Instant.now());
    DiscordNotification completedUndispatched =
        saveNotification(DiscordNotificationStatus.COMPLETED, null);
    DiscordNotification completedDispatched =
        saveNotification(DiscordNotificationStatus.COMPLETED, Instant.now());
    DiscordNotification failedUndispatched =
        saveNotification(DiscordNotificationStatus.FAILED, null);
    DiscordNotification failedDispatched =
        saveNotification(DiscordNotificationStatus.FAILED, Instant.now());

    List<DiscordNotification> result =
        discordNotificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result)
        .hasSize(1)
        .containsExactly(pendingUndispatched)
        .doesNotContain(pendingDispatched)
        .doesNotContain(completedUndispatched)
        .doesNotContain(completedDispatched)
        .doesNotContain(failedUndispatched)
        .doesNotContain(failedDispatched);

    assertThat(result)
        .allSatisfy(
            n -> {
              assertThat(n.getStatus()).isEqualTo(DiscordNotificationStatus.PENDING);
              assertThat(n.getDispatchedAt()).isNull();
            });
  }

  @Test
  void findPendingShouldReturnEmptyWhenNoPendingUndispatchedExist() {
    saveNotification(DiscordNotificationStatus.COMPLETED, null);
    saveNotification(DiscordNotificationStatus.FAILED, Instant.now());
    saveNotification(DiscordNotificationStatus.PENDING, Instant.now());

    List<DiscordNotification> result =
        discordNotificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findPendingShouldReturnEmptyWhenTableIsEmpty() {
    List<DiscordNotification> result =
        discordNotificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findPendingShouldReturnMultiplePendingUndispatched() {
    DiscordNotification first = saveNotification(DiscordNotificationStatus.PENDING, null);
    DiscordNotification second = saveNotification(DiscordNotificationStatus.PENDING, null);
    saveNotification(DiscordNotificationStatus.FAILED, null);
    saveNotification(DiscordNotificationStatus.COMPLETED, Instant.now());

    List<DiscordNotification> result =
        discordNotificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).hasSize(2).containsExactlyInAnyOrder(first, second);
  }

  @Test
  void findPendingShouldRespectPageableLimit() {
    saveNotification(DiscordNotificationStatus.PENDING, null);
    saveNotification(DiscordNotificationStatus.PENDING, null);
    saveNotification(DiscordNotificationStatus.PENDING, null);

    List<DiscordNotification> firstPage =
        discordNotificationRepository.findPending(PageRequest.of(0, 2));
    List<DiscordNotification> secondPage =
        discordNotificationRepository.findPending(PageRequest.of(1, 2));

    assertThat(firstPage).hasSize(2);
    assertThat(secondPage).hasSize(1);
  }

  @Test
  void findPendingShouldOrderByCreatedAtAscending() throws Exception {
    DiscordNotification first = saveNotification(DiscordNotificationStatus.PENDING, null);
    Thread.sleep(10);
    DiscordNotification second = saveNotification(DiscordNotificationStatus.PENDING, null);
    Thread.sleep(10);
    DiscordNotification third = saveNotification(DiscordNotificationStatus.PENDING, null);

    List<DiscordNotification> result =
        discordNotificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).containsExactly(first, second, third);
  }

  @Test
  void findPendingShouldExcludeCompletedEvenWhenDispatchedAtIsNull() {
    saveNotification(DiscordNotificationStatus.COMPLETED, null);

    List<DiscordNotification> result =
        discordNotificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).isEmpty();
  }

  @Test
  void findPendingShouldExcludePendingWhenDispatchedAtIsNotNull() {
    DiscordNotification dispatchedPending =
        saveNotification(DiscordNotificationStatus.PENDING, Instant.now());

    List<DiscordNotification> result =
        discordNotificationRepository.findPending(Pageable.ofSize(10));

    assertThat(result).doesNotContain(dispatchedPending).isEmpty();
  }
}
