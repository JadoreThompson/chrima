package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.exception.SubscriptionBalanceNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SubscriptionServiceGetByIdTest extends AbstractSubscriptionServiceIntegrationBase {

  @Test
  void shouldGetById() {
    SubscriptionBalanceResponse created =
        createBalance("guild-1", "user-1", UUID.randomUUID(), 25.0, SubscriptionStatus.ACTIVE);

    SubscriptionBalanceResponse fetched = subscriptionService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getCreditAmount()).isEqualTo(25.0);
    assertThat(fetched.getStatus()).isEqualTo(SubscriptionStatus.ACTIVE);
  }

  @Test
  void shouldThrowWhenNotFound() {
    assertThatThrownBy(() -> subscriptionService.getById(UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceNotFoundException.class);
  }
}
