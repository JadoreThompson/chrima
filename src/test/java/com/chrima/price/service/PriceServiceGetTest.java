package com.chrima.price.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.exception.PriceNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class PriceServiceGetTest extends AbstractPriceServiceIntegrationBase {

  @Test
  void shouldGetScopedByWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 3.0, null, null, null);

    PriceResponse fetched = priceService.get(created.getId(), workspaceId);

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getWorkspaceId()).isEqualTo(workspaceId);
  }

  @Test
  void shouldThrowWhenGetWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 3.0, null, null, null);

    assertThatThrownBy(() -> priceService.get(created.getId(), UUID.randomUUID()))
        .isInstanceOf(PriceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> priceService.get(UUID.randomUUID(), UUID.randomUUID()))
        .isInstanceOf(PriceNotFoundException.class);
  }
}
