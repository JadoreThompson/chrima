package com.chrima.analytics.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.analytics.api.dto.AnalyticsSummary;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.transaction.api.enums.TransactionStatus;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class AnalyticsServiceGetSummaryTest extends AbstractAnalyticsServiceIntegrationBase {

  @Test
  void shouldReturnZeroWhenNoData() {
    UUID workspaceId = UUID.randomUUID();

    AnalyticsSummary summary = analyticsService.getSummary(workspaceId);

    assertThat(summary.getTotalRevenue()).isZero();
    assertThat(summary.getTotalActiveCustomers()).isZero();
    assertThat(summary.getTotalTransactions()).isZero();
  }

  @Test
  void shouldSumOnlyCompleteTransactionsForRevenue() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    createTransaction(
        productId, priceId, "user-1", "0xsender", 10.0, TransactionStatus.COMPLETE, 100);
    createTransaction(
        productId, priceId, "user-2", "0xsender", 25.5, TransactionStatus.COMPLETE, 200);
    createTransaction(
        productId, priceId, "user-3", "0xsender", 100.0, TransactionStatus.FAILED, 300);

    AnalyticsSummary summary = analyticsService.getSummary(workspaceId);

    assertThat(summary.getTotalRevenue()).isEqualTo(35.5);
    assertThat(summary.getTotalTransactions()).isEqualTo(2);
  }

  @Test
  void shouldCountDistinctActiveCustomers() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    // two ACTIVE for same platform user should count as 1, different user counts separately
    createSubscription("guild-1", "user-1", productId, SubscriptionStatus.ACTIVE, null, null);
    createSubscription(
        "guild-1", "user-1", UUID.randomUUID(), SubscriptionStatus.ACTIVE, null, null);
    // this second subscription has different product but still same workspace? need product in same
    // workspace
    // Use different externalId/product still counts same user distinct
    UUID productId2 = createProduct(workspaceId);
    createSubscription("guild-2", "user-1", productId2, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-1", "user-2", productId, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-3", "user-3", productId, SubscriptionStatus.EXPIRED, null, null);
    createSubscription("guild-4", "user-4", productId, SubscriptionStatus.CANCELLED, null, null);

    AnalyticsSummary summary = analyticsService.getSummary(workspaceId);

    // Only distinct ACTIVE: user-1 and user-2 => 2
    assertThat(summary.getTotalActiveCustomers()).isEqualTo(2);
  }

  @Test
  void shouldIgnoreWorkspaceIsolation() {
    UUID workspaceId = UUID.randomUUID();
    UUID otherWorkspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID otherProductId = createProduct(otherWorkspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    UUID otherPriceId = createPrice(otherWorkspaceId, otherProductId);
    createTransaction(
        productId, priceId, "user-1", "0xsender", 50.0, TransactionStatus.COMPLETE, 100);
    createTransaction(
        otherProductId, otherPriceId, "user-2", "0xsender", 999.0, TransactionStatus.COMPLETE, 100);
    createSubscription("guild-1", "user-1", productId, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-1", "user-2", otherProductId, SubscriptionStatus.ACTIVE, null, null);

    AnalyticsSummary summary = analyticsService.getSummary(workspaceId);

    assertThat(summary.getTotalRevenue()).isEqualTo(50.0);
    assertThat(summary.getTotalTransactions()).isEqualTo(1);
    assertThat(summary.getTotalActiveCustomers()).isEqualTo(1);
  }

  @Test
  void shouldIncludeMultipleProductsInSameWorkspace() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId1 = createProduct(workspaceId);
    UUID productId2 = createProduct(workspaceId);
    UUID priceId1 = createPrice(workspaceId, productId1);
    UUID priceId2 = createPrice(workspaceId, productId2);
    createTransaction(
        productId1, priceId1, "user-1", "0xsender", 10.0, TransactionStatus.COMPLETE, 100);
    createTransaction(
        productId2, priceId2, "user-2", "0xsender", 20.0, TransactionStatus.COMPLETE, 100);
    createSubscription("guild-1", "user-a", productId1, SubscriptionStatus.ACTIVE, null, null);
    createSubscription("guild-2", "user-b", productId2, SubscriptionStatus.ACTIVE, null, null);

    AnalyticsSummary summary = analyticsService.getSummary(workspaceId);

    assertThat(summary.getTotalRevenue()).isEqualTo(30.0);
    assertThat(summary.getTotalTransactions()).isEqualTo(2);
    assertThat(summary.getTotalActiveCustomers()).isEqualTo(2);
  }
}
