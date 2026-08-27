package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.exception.SubscriptionBalanceNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SubscriptionServiceGetTest extends AbstractSubscriptionServiceIntegrationBase {

  @Test
  void shouldGetByExternalIdPlatformUserIdAndProductId() {
    UUID productId = UUID.randomUUID();
    SubscriptionBalanceResponse created =
        createBalance("guild-1", "user-1", productId, 75.0, SubscriptionStatus.ACTIVE);

    SubscriptionBalanceResponse fetched = subscriptionService.get("guild-1", "user-1", productId);

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getCreditAmount()).isEqualTo(75.0);
    assertThat(fetched.getStatus()).isEqualTo(SubscriptionStatus.ACTIVE);
  }

  @Test
  void shouldThrowWhenGroupNotFound() {
    assertThatThrownBy(() -> subscriptionService.get("guild-1", "user-1", UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceNotFoundException.class);
  }
}
