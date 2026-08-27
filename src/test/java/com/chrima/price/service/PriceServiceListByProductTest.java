package com.chrima.price.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.chrima.price.api.dto.PriceResponse;
import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

class PriceServiceListByProductTest extends AbstractPriceServiceIntegrationBase {

  @Test
  void shouldListByProductReturnsPrices() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    PriceResponse p1 =
        priceService.create(
            workspaceId, productId, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);
    PriceResponse p2 =
        priceService.create(
            workspaceId, productId, PriceType.RECURRING, Currency.USD, 2.0, null, null, null);

    Page<PriceResponse> result = priceService.listByProduct(productId, PageRequest.of(0, 10));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.getContent())
        .extracting(PriceResponse::getId)
        .containsExactlyInAnyOrder(p1.getId(), p2.getId());
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getTotalElements()).isEqualTo(2);
  }

  @Test
  void shouldPaginate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      priceService.create(
          workspaceId, productId, PriceType.ONE_TIME, Currency.USD, i + 1.0, null, null, null);
    }

    Page<PriceResponse> result = priceService.listByProduct(productId, PageRequest.of(0, 2));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.hasNext()).isTrue();
    assertThat(result.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldPaginateSecondPage() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      priceService.create(
          workspaceId, productId, PriceType.ONE_TIME, Currency.USD, i + 1.0, null, null, null);
    }

    Page<PriceResponse> page1 = priceService.listByProduct(productId, PageRequest.of(0, 2));
    Page<PriceResponse> page2 = priceService.listByProduct(productId, PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  @Test
  void shouldListByProductIsolatedByProduct() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId1 = mockProductExists(UUID.randomUUID());
    UUID productId2 = mockProductExists(UUID.randomUUID());
    priceService.create(
        workspaceId, productId1, PriceType.ONE_TIME, Currency.USD, 1.0, null, null, null);
    priceService.create(
        workspaceId, productId2, PriceType.ONE_TIME, Currency.USD, 2.0, null, null, null);

    Page<PriceResponse> result1 = priceService.listByProduct(productId1, PageRequest.of(0, 10));
    Page<PriceResponse> result2 = priceService.listByProduct(productId2, PageRequest.of(0, 10));

    assertThat(result1.getContent()).hasSize(1);
    assertThat(result1.getContent().get(0).getAmount()).isEqualTo(1.0);
    assertThat(result2.getContent()).hasSize(1);
    assertThat(result2.getContent().get(0).getAmount()).isEqualTo(2.0);
  }

  @Test
  void shouldReturnEmptyWhenNoPrices() {
    UUID productId = mockProductExists(UUID.randomUUID());

    Page<PriceResponse> result = priceService.listByProduct(productId, PageRequest.of(0, 10));

    assertThat(result.getContent()).isEmpty();
    assertThat(result.getTotalElements()).isEqualTo(0);
  }

  @Test
  void shouldThrowWhenProductNotFoundOnList() {
    when(productService.getById(any())).thenThrow(new RuntimeException("Product not found"));

    assertThatThrownBy(() -> priceService.listByProduct(UUID.randomUUID(), PageRequest.of(0, 10)))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("Product not found");
  }

  @Test
  void shouldSupportLegacyPageAndLimitOverload() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID productId = mockProductExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      priceService.create(
          workspaceId, productId, PriceType.ONE_TIME, Currency.USD, i + 1.0, null, null, null);
    }

    Page<PriceResponse> page1 = priceService.listByProduct(productId, 1, 2);
    Page<PriceResponse> page2 = priceService.listByProduct(productId, 2, 2);

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }
}
