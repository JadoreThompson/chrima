package com.chrima.price.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.price.event.PriceUpdatedEvent;
import com.chrima.price.exception.PriceValidationException;
import com.chrima.price.model.Price;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class PriceServiceCreateTest extends AbstractPriceServiceIntegrationBase {

  @Test
  void shouldCreatePriceAndPersist() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());

    PriceResponse price =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 9.99, null, null, null);

    assertThat(price.getId()).isNotNull();
    assertThat(price.getWorkspaceId()).isEqualTo(workspaceId);
    assertThat(price.getProductId()).isEqualTo(productId);
    assertThat(price.getType()).isEqualTo(PriceType.ONE_TIME);
    assertThat(price.getCurrency()).isEqualTo(Currency.USD);
    assertThat(price.getAmount()).isEqualTo(9.99);
    assertThat(price.getRecurringInterval()).isNull();
    assertThat(price.getRecurringIntervalCount()).isNull();
    assertThat(price.getTrialPeriodDays()).isNull();
    assertThat(price.getCreatedAt()).isNotNull();
    assertThat(price.getUpdatedAt()).isNotNull();

    Price row = priceRepository.findById(price.getId()).orElseThrow();
    assertThat(row.getWorkspaceId()).isEqualTo(workspaceId);
    assertThat(row.getProductId()).isEqualTo(productId);
    assertThat(row.getType()).isEqualTo(PriceType.ONE_TIME);
    assertThat(row.getCurrency()).isEqualTo(Currency.USD);
    assertThat(row.getAmount()).isEqualTo(9.99);
  }

  @Test
  void shouldCreateRecurringPrice() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());

    PriceResponse price =
        priceService.create(
            workspaceId,
            productId,
            PriceType.RECURRING,
            Currency.USD,
            19.99,
            RecurringInterval.MONTH,
            1,
            7);

    assertThat(price.getType()).isEqualTo(PriceType.RECURRING);
    assertThat(price.getRecurringInterval()).isEqualTo(RecurringInterval.MONTH);
    assertThat(price.getRecurringIntervalCount()).isEqualTo(1);
    assertThat(price.getTrialPeriodDays()).isEqualTo(7);
  }

  @Test
  void shouldPublishPriceUpdatedEventOnCreate() throws Exception {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());

    PriceResponse price =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 5.0, null, null, null);

    verify(eventService).publish(eq("price.updated"), any(PriceUpdatedEvent.class), anyString());
    assertThat(price.getId()).isNotNull();
  }

  @Test
  void shouldThrowWhenAmountIsZeroOnCreate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());

    assertThatThrownBy(
            () ->
                priceService.create(
                    workspaceId,
                    productId,
                    PriceType.ONE_TIME,
                    Currency.USD,
                    0.0,
                    null,
                    null,
                    null))
        .isInstanceOf(PriceValidationException.class)
        .hasMessageContaining("Amount must be greater than zero");
  }

  @Test
  void shouldThrowWhenAmountIsNegativeOnCreate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());

    assertThatThrownBy(
            () ->
                priceService.create(
                    workspaceId,
                    productId,
                    PriceType.ONE_TIME,
                    Currency.USD,
                    -1.0,
                    null,
                    null,
                    null))
        .isInstanceOf(PriceValidationException.class)
        .hasMessageContaining("Amount must be greater than zero");
  }

  @Test
  void shouldThrowWhenWorkspaceNotFoundOnCreate() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = mockProductExists(UUID.randomUUID());
    when(workspaceService.getById(any())).thenThrow(new RuntimeException("Workspace not found"));

    assertThatThrownBy(
            () ->
                priceService.create(
                    workspaceId,
                    productId,
                    PriceType.ONE_TIME,
                    Currency.USD,
                    1.0,
                    null,
                    null,
                    null))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("Workspace not found");
  }

  @Test
  void shouldThrowWhenProductNotFoundOnCreate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = UUID.randomUUID();
    when(productService.getById(any())).thenThrow(new RuntimeException("Product not found"));

    assertThatThrownBy(
            () ->
                priceService.create(
                    workspaceId,
                    productId,
                    PriceType.ONE_TIME,
                    Currency.USD,
                    1.0,
                    null,
                    null,
                    null))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("Product not found");
  }
}
