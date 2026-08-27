package com.chrima.price.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.clearInvocations;
import static org.mockito.Mockito.verify;

import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.price.event.PriceUpdatedEvent;
import com.chrima.price.exception.PriceNotFoundException;
import com.chrima.price.exception.PriceValidationException;
import com.chrima.price.model.Price;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class PriceServiceUpdateTest extends AbstractPriceServiceIntegrationBase {

  @Test
  void shouldUpdateAmount() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);

    PriceResponse updated =
        priceService.update(created.getId(), workspaceId, null, 7.5, null, null, null);

    assertThat(updated.getAmount()).isEqualTo(7.5);
    Price row = priceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getAmount()).isEqualTo(7.5);
  }

  @Test
  void shouldUpdateCurrency() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);

    PriceResponse updated =
        priceService.update(created.getId(), workspaceId, Currency.USD, null, null, null, null);

    assertThat(updated.getCurrency()).isEqualTo(Currency.USD);
  }

  @Test
  void shouldUpdateRecurringFields() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);

    PriceResponse updated =
        priceService.update(
            created.getId(), workspaceId, null, null, RecurringInterval.MONTH, 2, 14);

    assertThat(updated.getRecurringInterval()).isEqualTo(RecurringInterval.MONTH);
    assertThat(updated.getRecurringIntervalCount()).isEqualTo(2);
    assertThat(updated.getTrialPeriodDays()).isEqualTo(14);
    Price row = priceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getRecurringInterval()).isEqualTo(RecurringInterval.MONTH);
    assertThat(row.getRecurringIntervalCount()).isEqualTo(2);
    assertThat(row.getTrialPeriodDays()).isEqualTo(14);
  }

  @Test
  void shouldUpdateAllFields() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId,
            productId,
            PriceType.ONE_TIME,
            Currency.USD,
            1.0,
            RecurringInterval.DAY,
            1,
            3);

    PriceResponse updated =
        priceService.update(
            created.getId(), workspaceId, Currency.USD, 99.99, RecurringInterval.MONTH, 2, 14);

    assertThat(updated.getAmount()).isEqualTo(99.99);
    assertThat(updated.getRecurringInterval()).isEqualTo(RecurringInterval.MONTH);
    assertThat(updated.getRecurringIntervalCount()).isEqualTo(2);
    assertThat(updated.getTrialPeriodDays()).isEqualTo(14);
  }

  @Test
  void shouldPublishPriceUpdatedEventOnUpdate() throws Exception {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);
    clearInvocations(eventService);

    priceService.update(created.getId(), workspaceId, null, 8.0, null, null, null);

    verify(eventService).publish(eq("price.updated"), any(PriceUpdatedEvent.class), anyString());
  }

  @Test
  void shouldThrowWhenAmountNotPositiveOnUpdate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);

    assertThatThrownBy(
            () -> priceService.update(created.getId(), workspaceId, null, 0.0, null, null, null))
        .isInstanceOf(PriceValidationException.class)
        .hasMessageContaining("Amount must be greater than zero");
  }

  @Test
  void shouldThrowWhenUpdatePriceNotFound() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    assertThatThrownBy(
            () -> priceService.update(UUID.randomUUID(), workspaceId, null, 1.0, null, null, null))
        .isInstanceOf(PriceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenUpdateWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);

    assertThatThrownBy(
            () ->
                priceService.update(
                    created.getId(), UUID.randomUUID(), null, 1.0, null, null, null))
        .isInstanceOf(PriceNotFoundException.class);

    Price row = priceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getAmount()).isEqualTo(1.0);
  }
}
