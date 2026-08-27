package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

class ProductServiceListByWorkspaceTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldListByWorkspaceReturnsProducts() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse p1 =
        productService.create(
            workspaceId, "product-a", null, walletId, FulfilmentType.INVITE, null, null);
    ProductResponse p2 =
        productService.create(
            workspaceId, "product-b", null, walletId, FulfilmentType.ROLE, null, null);

    Page<ProductResponse> result =
        productService.listByWorkspace(workspaceId, PageRequest.of(0, 10));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.getContent())
        .extracting(ProductResponse::getId)
        .containsExactlyInAnyOrder(p1.getId(), p2.getId());
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getNumber()).isEqualTo(0);
    assertThat(result.getTotalElements()).isEqualTo(2);
  }

  @Test
  void shouldPaginate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      productService.create(
          workspaceId, "product-" + i, null, walletId, FulfilmentType.INVITE, null, null);
    }

    Page<ProductResponse> result =
        productService.listByWorkspace(workspaceId, PageRequest.of(0, 2));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.hasNext()).isTrue();
    assertThat(result.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldReturnEmptyWhenNoProducts() {
    Page<ProductResponse> result =
        productService.listByWorkspace(UUID.randomUUID(), PageRequest.of(0, 10));

    assertThat(result.getContent()).isEmpty();
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getTotalElements()).isEqualTo(0);
  }

  @Test
  void shouldPaginateSecondPage() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      productService.create(
          workspaceId, "product", null, walletId, FulfilmentType.INVITE, null, null);
    }

    Page<ProductResponse> page1 = productService.listByWorkspace(workspaceId, PageRequest.of(0, 2));
    Page<ProductResponse> page2 = productService.listByWorkspace(workspaceId, PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  @Test
  void shouldListByWorkspaceIsolatedByWorkspace() {
    UUID workspaceId1 = mockWorkspaceExists(UUID.randomUUID());
    UUID wallet1 = mockWalletExists(UUID.randomUUID());
    UUID workspaceId2 = mockWorkspaceExists(UUID.randomUUID());
    UUID wallet2 = mockWalletExists(UUID.randomUUID());
    productService.create(
        workspaceId1, "ws1-product", null, wallet1, FulfilmentType.INVITE, null, null);
    productService.create(
        workspaceId2, "ws2-product", null, wallet2, FulfilmentType.INVITE, null, null);

    Page<ProductResponse> result1 =
        productService.listByWorkspace(workspaceId1, PageRequest.of(0, 10));
    Page<ProductResponse> result2 =
        productService.listByWorkspace(workspaceId2, PageRequest.of(0, 10));

    assertThat(result1.getContent()).hasSize(1);
    assertThat(result1.getContent().get(0).getName()).isEqualTo("ws1-product");
    assertThat(result2.getContent()).hasSize(1);
    assertThat(result2.getContent().get(0).getName()).isEqualTo("ws2-product");
  }

  @Test
  void shouldSupportLegacyPageAndLimitOverload() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      productService.create(
          workspaceId, "product", null, walletId, FulfilmentType.INVITE, null, null);
    }

    Page<ProductResponse> page1 = productService.listByWorkspace(workspaceId, 1, 2);
    Page<ProductResponse> page2 = productService.listByWorkspace(workspaceId, 2, 2);

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }
}
