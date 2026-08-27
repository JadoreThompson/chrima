package com.chrima.subscription.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.exception.SubscriptionBalanceNotFoundException;
import com.chrima.subscription.exception.SubscriptionBalanceValidationException;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class SubscriptionServiceProcessCycleTest extends AbstractSubscriptionServiceIntegrationBase {

  @Test
  void shouldProcessDailyCycle() {
    UUID productId = UUID.randomUUID();
    UUID transactionId = UUID.randomUUID();
    SubscriptionBalanceResponse created =
        createBalance("1", "1", productId, 100.0, SubscriptionStatus.ACTIVE);
    long before = Instant.now().getEpochSecond();

    SubscriptionBalanceResponse updated =
        subscriptionService.processCycle(
            "1", "1", productId, 10.0, RecurringInterval.DAY, 2, transactionId);

    assertThat(updated.getId()).isEqualTo(created.getId());
    assertThat(updated.getCreditAmount()).isEqualTo(90.0);
    assertThat(updated.getCycleStart()).isNotNull();
    assertThat(updated.getCycleStart()).isBetween((int) before, (int) before + 5);
    assertThat(updated.getCycleEnd()).isEqualTo(updated.getCycleStart() + 2 * 86400);
    assertThat(updated.getLastProcessedTx()).isEqualTo(transactionId);
  }

  @Test
  void shouldProcessMonthlyCycle() {
    UUID productId = UUID.randomUUID();
    UUID transactionId = UUID.randomUUID();
    createBalance("1", "1", productId, 100.0, SubscriptionStatus.ACTIVE);
    long before = Instant.now().getEpochSecond();

    SubscriptionBalanceResponse updated =
        subscriptionService.processCycle(
            "1", "1", productId, 30.0, RecurringInterval.MONTH, 1, transactionId);

    assertThat(updated.getCreditAmount()).isEqualTo(70.0);
    assertThat(updated.getCycleStart()).isBetween((int) before, (int) before + 5);
    assertThat(updated.getCycleEnd()).isEqualTo(updated.getCycleStart() + 2592000);
    assertThat(updated.getLastProcessedTx()).isEqualTo(transactionId);
  }

  @Test
  void shouldThrowWhenAmountIsZeroOnProcessCycle() {
    createBalance("1", "1", UUID.randomUUID(), 100.0, SubscriptionStatus.ACTIVE);

    assertThatThrownBy(
            () ->
                subscriptionService.processCycle(
                    "1", "1", UUID.randomUUID(), 0.0, RecurringInterval.DAY, 1, UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceValidationException.class)
        .hasMessageContaining("Amount must be greater than zero");
  }

  @Test
  void shouldThrowWhenTransactionIdMissingOnProcessCycle() {
    createBalance("1", "1", UUID.randomUUID(), 100.0, SubscriptionStatus.ACTIVE);

    assertThatThrownBy(
            () ->
                subscriptionService.processCycle(
                    "1", "1", UUID.randomUUID(), 10.0, RecurringInterval.DAY, 1, null))
        .isInstanceOf(SubscriptionBalanceValidationException.class)
        .hasMessageContaining("Transaction ID must be provided");
  }

  @Test
  void shouldThrowWhenGroupNotFoundOnProcessCycle() {
    assertThatThrownBy(
            () ->
                subscriptionService.processCycle(
                    "1", "1", UUID.randomUUID(), 10.0, RecurringInterval.DAY, 1, UUID.randomUUID()))
        .isInstanceOf(SubscriptionBalanceNotFoundException.class);
  }
}
