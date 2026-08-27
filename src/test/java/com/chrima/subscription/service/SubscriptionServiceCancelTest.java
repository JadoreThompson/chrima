package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;

import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.event.SubscriptionCancelledEvent;
import com.chrima.subscription.exception.SubscriptionBalanceAlreadyCancelledException;
import com.chrima.subscription.exception.SubscriptionBalanceNotFoundException;
import com.chrima.subscription.model.SubscriptionBalance;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SubscriptionServiceCancelTest extends AbstractSubscriptionServiceIntegrationBase {

  @Test
  void shouldCancelBalanceAndPublishEvent() throws Exception {
    UUID productId = UUID.randomUUID();
    SubscriptionBalanceResponse created =
        createBalance("1", "1", productId, 40.0, SubscriptionStatus.ACTIVE);

    SubscriptionBalanceResponse cancelled = subscriptionService.cancel(created.getId());

    assertThat(cancelled.getId()).isEqualTo(created.getId());
    assertThat(cancelled.getStatus()).isEqualTo(SubscriptionStatus.CANCELLED);

    verify(eventService)
        .publish(eq("subscription.cancelled"), any(SubscriptionCancelledEvent.class), anyString());

    SubscriptionBalance row = subscriptionBalanceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getStatus()).isEqualTo(SubscriptionStatus.CANCELLED);
  }

  @Test
  void shouldThrowWhenAlreadyCancelled() {
    UUID productId = UUID.randomUUID();
    SubscriptionBalanceResponse created =
        createBalance("1", "1", productId, 40.0, SubscriptionStatus.CANCELLED);

    assertThatThrownBy(() -> subscriptionService.cancel(created.getId()))
        .isInstanceOf(SubscriptionBalanceAlreadyCancelledException.class)
        .hasMessageContaining("already cancelled");
  }

  @Test
  void shouldThrowWhenNotFoundOnCancel() {
    assertThatThrownBy(() -> subscriptionService.cancel(UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceNotFoundException.class);
  }
}
