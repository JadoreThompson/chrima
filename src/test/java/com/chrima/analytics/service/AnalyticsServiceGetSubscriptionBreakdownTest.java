package com.chrima.analytics.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.analytics.api.dto.SubscriptionAnalytics;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class AnalyticsServiceGetSubscriptionBreakdownTest extends AbstractAnalyticsServiceIntegrationBase {

  @Test
  void shouldReturnZeroWhenNoSubscriptions() {
    UUID workspaceId = UUID.randomUUID();

    SubscriptionAnalytics analytics = analyticsService.getSubscriptionBreakdown(workspaceId);

    assertThat(analytics.getActive()).isZero();
    assertThat(analytics.getExpired()).isZero();
    assertThat(analytics.getCancelled()).isZero();
    assertThat(analytics.getExpiring()).isZero();
  }

  @Test
  void shouldCountByStatus() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    createSubscription("guild-1", "user-1", productId, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-2", "user-2", productId, SubscriptionStatus.EXPIRED, null, null);
    createSubscription("guild-3", "user-3", productId, SubscriptionStatus.CANCELLED, null, null);
    createSubscription("guild-4", "user-4", productId, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-5", "user-5", productId, SubscriptionStatus.INCOMPLETE, null, null);

    SubscriptionAnalytics analytics = analyticsService.getSubscriptionBreakdown(workspaceId);

    assertThat(analytics.getActive()).isEqualTo(2);
    assertThat(analytics.getExpired()).isEqualTo(1);
    assertThat(analytics.getCancelled()).isEqualTo(1);
    // INCOMPLETE not counted in active/expired/cancelled
    assertThat(analytics.getExpiring()).isZero();
  }

  @Test
  void shouldCountExpiringWithinSevenDays() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    long now = nowEpoch();
    int expiringSoon = (int) (now + 3 * 86400); // 3 days
    int expiringLater = (int) (now + 10 * 86400); // 10 days
    int alreadyExpired = (int) (now - 86400);
    // ACTIVE with cycleEnd within 7 days => expiring
    createSubscription(
        "guild-1", "user-1", productId, SubscriptionStatus.ACTIVE, null, expiringSoon);
    // ACTIVE but beyond 7 days => not expiring
    createSubscription(
        "guild-2", "user-2", productId, SubscriptionStatus.ACTIVE, null, expiringLater);
    // ACTIVE with null cycleEnd => not expiring
    createSubscription("guild-3", "user-3", productId, SubscriptionStatus.ACTIVE, null, null);
    // EXPIRED with expiringSoon should not count towards expiring (only ACTIVE)
    createSubscription(
        "guild-4", "user-4", productId, SubscriptionStatus.EXPIRED, null, expiringSoon);
    // ACTIVE already expired but within threshold? cycleEnd in past <= threshold, should count as
    // expiring per logic
    createSubscription(
        "guild-5", "user-5", productId, SubscriptionStatus.ACTIVE, null, alreadyExpired);

    SubscriptionAnalytics analytics = analyticsService.getSubscriptionBreakdown(workspaceId);

    assertThat(analytics.getActive()).isEqualTo(4);
    assertThat(analytics.getExpired()).isEqualTo(1);
    // expiring: guild-1 + guild-5 = 2
    assertThat(analytics.getExpiring()).isEqualTo(2);
  }

  @Test
  void shouldIsolateWorkspace() {
    UUID workspaceId = UUID.randomUUID();
    UUID otherWorkspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID otherProductId = createProduct(otherWorkspaceId);
    createSubscription("guild-1", "user-1", productId, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-2", "user-2", otherProductId, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-3", "user-3", otherProductId, SubscriptionStatus.EXPIRED, null, null);

    SubscriptionAnalytics analytics = analyticsService.getSubscriptionBreakdown(workspaceId);

    assertThat(analytics.getActive()).isEqualTo(1);
    assertThat(analytics.getExpired()).isZero();
    assertThat(analytics.getCancelled()).isZero();
  }

  @Test
  void shouldCountMultipleProductsInSameWorkspace() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId1 = createProduct(workspaceId);
    UUID productId2 = createProduct(workspaceId);
    createSubscription("guild-1", "user-1", productId1, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-2", "user-2", productId2, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-3", "user-3", productId1, SubscriptionStatus.CANCELLED, null, null);

    SubscriptionAnalytics analytics = analyticsService.getSubscriptionBreakdown(workspaceId);

    assertThat(analytics.getActive()).isEqualTo(2);
    assertThat(analytics.getCancelled()).isEqualTo(1);
  }
}
