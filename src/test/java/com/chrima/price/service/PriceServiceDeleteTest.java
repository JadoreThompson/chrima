package com.chrima.price.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.exception.PriceNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class PriceServiceDeleteTest extends AbstractPriceServiceIntegrationBase {

  @Test
  void shouldDeletePriceAndVerifyGone() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);

    priceService.delete(created.getId(), workspaceId);

    assertThat(priceRepository.findById(created.getId())).isEmpty();
    assertThatThrownBy(() -> priceService.getById(created.getId()))
        .isInstanceOf(PriceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteNotFound() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    assertThatThrownBy(() -> priceService.delete(UUID.randomUUID(), workspaceId))
        .isInstanceOf(PriceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse created =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);

    assertThatThrownBy(() -> priceService.delete(created.getId(), UUID.randomUUID()))
        .isInstanceOf(PriceNotFoundException.class);

    assertThat(priceRepository.findById(created.getId())).isPresent();
  }
}
