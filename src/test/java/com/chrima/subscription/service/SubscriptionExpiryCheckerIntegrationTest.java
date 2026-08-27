package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.notification.discord.api.IDiscordNotificationService;
import com.chrima.product.api.IProductService;
import com.chrima.product.api.dto.ProductResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.config.SubscriptionExpiryConfig;
import com.chrima.subscription.model.SubscriptionBalance;
import com.chrima.subscription.notification.SubscriptionExpiredNotificationContent;
import com.chrima.subscription.notification.SubscriptionExpiringNotificationContent;
import com.chrima.subscription.repository.SubscriptionBalanceRepository;
import com.chrima.workspace.api.IWorkspaceService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.testcontainers.containers.PostgreSQLContainer;

@DataJpaTest
@Import({SubscriptionExpiryChecker.class, SubscriptionExpiryConfig.class})
class SubscriptionExpiryCheckerIntegrationTest {

  @SuppressWarnings("resource")
  static final PostgreSQLContainer<?> postgres =
      new PostgreSQLContainer<>("postgres:16-alpine")
          .withDatabaseName("chrima")
          .withUsername("postgres")
          .withPassword("password");

  static {
    postgres.start();
  }

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
    registry.add("spring.datasource.driver-class-name", postgres::getDriverClassName);
  }

  @Autowired private SubscriptionExpiryChecker subscriptionExpiryChecker;

  @Autowired private SubscriptionBalanceRepository subscriptionBalanceRepository;

  @MockitoBean private IProductService productService;

  @MockitoBean private IWorkspaceService workspaceService;

  @MockitoBean private IDiscordNotificationService discordNotificationService;

  @AfterEach
  void tearDown() {
    subscriptionBalanceRepository.deleteAll();
  }

  private SubscriptionBalance saveBalance(
      SubscriptionStatus status, int cycleEnd, int attemptCount, Integer lastNotifiedAt) {
    return subscriptionBalanceRepository.save(
        SubscriptionBalance.builder()
            .externalId("1")
            .platformUserId("1")
            .productId(UUID.randomUUID())
            .creditAmount(50.0)
            .cycleStart(cycleEnd - 86400)
            .cycleEnd(cycleEnd)
            .status(status)
            .attemptCount(attemptCount)
            .lastNotifiedAt(lastNotifiedAt)
            .build());
  }

  private void mockProductAndWorkspace() {
    when(productService.getById(any()))
        .thenReturn(ProductResponse.builder().id(UUID.randomUUID()).name("Pro").build());
    when(workspaceService.getById(any()))
        .thenReturn(
            WorkspaceResponse.builder().externalId("12345").notificationChannelId("67890").build());
  }

  @Test
  void shouldNotifyExpiredBalanceAndMarkExpired() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance = saveBalance(SubscriptionStatus.ACTIVE, (int) now - 100, 0, null);
    mockProductAndWorkspace();

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService)
        .publish(
            eq(12345L),
            eq(67890L),
            eq("subscription.expired"),
            any(SubscriptionExpiredNotificationContent.class),
            anyString());

    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getStatus()).isEqualTo(SubscriptionStatus.EXPIRED);
    assertThat(reloaded.getAttemptCount()).isEqualTo(1);
    assertThat(reloaded.getLastNotifiedAt()).isNotNull();
  }

  @Test
  void shouldNotifyExpiringBalanceAndRemainActive() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance = saveBalance(SubscriptionStatus.ACTIVE, (int) now + 3600, 0, null);
    mockProductAndWorkspace();

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService)
        .publish(
            eq(12345L),
            eq(67890L),
            eq("subscription.expiring"),
            any(SubscriptionExpiringNotificationContent.class),
            anyString());

    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getStatus()).isEqualTo(SubscriptionStatus.ACTIVE);
    assertThat(reloaded.getAttemptCount()).isEqualTo(1);
    assertThat(reloaded.getLastNotifiedAt()).isNotNull();
  }

  @Test
  void shouldSkipCancelledExpiredBalance() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance =
        saveBalance(SubscriptionStatus.CANCELLED, (int) now - 100, 0, null);
    mockProductAndWorkspace();

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService, never())
        .publish(any(), any(), anyString(), any(), anyString());
    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getStatus()).isEqualTo(SubscriptionStatus.CANCELLED);
    assertThat(reloaded.getAttemptCount()).isZero();
  }

  @Test
  void shouldSkipBalanceAtMaxAttempts() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance = saveBalance(SubscriptionStatus.ACTIVE, (int) now - 100, 2, null);
    mockProductAndWorkspace();

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService, never())
        .publish(any(), any(), anyString(), any(), anyString());
    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getAttemptCount()).isEqualTo(2);
  }

  @Test
  void shouldSkipBalanceWithinNotificationCooldown() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance =
        saveBalance(SubscriptionStatus.ACTIVE, (int) now - 100, 0, (int) now);
    mockProductAndWorkspace();

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService, never())
        .publish(any(), any(), anyString(), any(), anyString());
    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getAttemptCount()).isZero();
  }

  @Test
  void shouldSkipExpiringBalanceOutsideWindow() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance =
        saveBalance(SubscriptionStatus.ACTIVE, (int) now + 13 * 3600, 0, null);
    mockProductAndWorkspace();

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService, never())
        .publish(any(), any(), anyString(), any(), anyString());
    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getAttemptCount()).isZero();
  }

  @Test
  void shouldSkipWhenProductNotFound() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance = saveBalance(SubscriptionStatus.ACTIVE, (int) now - 100, 0, null);
    when(productService.getById(any())).thenThrow(new RuntimeException("Product not found"));

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService, never())
        .publish(any(), any(), anyString(), any(), anyString());
    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getAttemptCount()).isZero();
    assertThat(reloaded.getLastNotifiedAt()).isNull();
  }

  @Test
  void shouldSkipWhenWorkspaceNotFound() {
    long now = Instant.now().getEpochSecond();
    SubscriptionBalance balance = saveBalance(SubscriptionStatus.ACTIVE, (int) now - 100, 0, null);
    when(productService.getById(any()))
        .thenReturn(ProductResponse.builder().id(UUID.randomUUID()).name("Pro").build());
    when(workspaceService.getById(any())).thenThrow(new RuntimeException("Workspace not found"));

    subscriptionExpiryChecker.checkExpirations();

    verify(discordNotificationService, never())
        .publish(any(), any(), anyString(), any(), anyString());
    SubscriptionBalance reloaded =
        subscriptionBalanceRepository.findById(balance.getId()).orElseThrow();
    assertThat(reloaded.getAttemptCount()).isZero();
  }
}
