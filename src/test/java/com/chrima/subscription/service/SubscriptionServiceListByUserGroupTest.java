package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SubscriptionServiceListByUserGroupTest extends AbstractSubscriptionServiceIntegrationBase {

  @Test
  void shouldListAllBalancesForUserGroup() {
    UUID productA = UUID.randomUUID();
    UUID productB = UUID.randomUUID();
    createBalance("1", "1", productA, 10.0, SubscriptionStatus.ACTIVE);
    createBalance("1", "1", productB, 20.0, SubscriptionStatus.ACTIVE);
    createBalance("1", "2", productA, 30.0, SubscriptionStatus.ACTIVE);
    createBalance("2", "1", productA, 40.0, SubscriptionStatus.ACTIVE);

    List<SubscriptionBalanceResponse> balances = subscriptionService.listByUserGroup(1L, 1L);

    assertThat(balances).hasSize(2);
    assertThat(balances)
        .extracting(SubscriptionBalanceResponse::getProductId)
        .containsExactlyInAnyOrder(productA, productB);
  }

  @Test
  void shouldReturnEmptyWhenNoBalances() {
    assertThat(subscriptionService.listByUserGroup(1L, 1L)).isEmpty();
  }
}
