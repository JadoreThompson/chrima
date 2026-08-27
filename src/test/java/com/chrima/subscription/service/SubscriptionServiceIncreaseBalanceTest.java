package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.exception.SubscriptionBalanceNotFoundException;
import com.chrima.subscription.exception.SubscriptionBalanceValidationException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SubscriptionServiceIncreaseBalanceTest extends AbstractSubscriptionServiceIntegrationBase {

  @Test
  void shouldIncreaseBalanceAndUpdateLastProcessedTx() {
    UUID productId = UUID.randomUUID();
    UUID transactionId = UUID.randomUUID();
    SubscriptionBalanceResponse created =
        createBalance("1", "1", productId, 50.0, SubscriptionStatus.ACTIVE);

    SubscriptionBalanceResponse updated =
        subscriptionService.increaseBalance("1", "1", productId, 25.0, transactionId);

    assertThat(updated.getId()).isEqualTo(created.getId());
    assertThat(updated.getCreditAmount()).isEqualTo(75.0);
    assertThat(updated.getLastProcessedTx()).isEqualTo(transactionId);

    SubscriptionBalanceResponse reloaded = subscriptionService.getById(created.getId());
    assertThat(reloaded.getCreditAmount()).isEqualTo(75.0);
    assertThat(reloaded.getLastProcessedTx()).isEqualTo(transactionId);
  }

  @Test
  void shouldThrowWhenAmountIsZeroOnIncrease() {
    createBalance("1", "1", UUID.randomUUID(), 50.0, SubscriptionStatus.ACTIVE);

    assertThatThrownBy(
            () ->
                subscriptionService.increaseBalance(
                    "1", "1", UUID.randomUUID(), 0.0, UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceValidationException.class)
        .hasMessageContaining("Amount must be greater than zero");
  }

  @Test
  void shouldThrowWhenAmountIsNegativeOnIncrease() {
    createBalance("1", "1", UUID.randomUUID(), 50.0, SubscriptionStatus.ACTIVE);

    assertThatThrownBy(
            () ->
                subscriptionService.increaseBalance(
                    "1", "1", UUID.randomUUID(), -5.0, UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceValidationException.class)
        .hasMessageContaining("Amount must be greater than zero");
  }

  @Test
  void shouldThrowWhenTransactionIdMissingOnIncrease() {
    createBalance("1", "1", UUID.randomUUID(), 50.0, SubscriptionStatus.ACTIVE);

    assertThatThrownBy(
            () -> subscriptionService.increaseBalance("1", "1", UUID.randomUUID(), 5.0, null))
        .isInstanceOf(SubscriptionBalanceValidationException.class)
        .hasMessageContaining("Transaction ID must be provided");
  }

  @Test
  void shouldThrowWhenGroupNotFoundOnIncrease() {
    assertThatThrownBy(
            () ->
                subscriptionService.increaseBalance(
                    "1", "1", UUID.randomUUID(), 5.0, UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceNotFoundException.class);
  }
}
