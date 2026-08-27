package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.exception.ProductNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceGetTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldGet() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "get-ws", "desc", walletId, FulfilmentType.INVITE, null, null);

    ProductResponse fetched = productService.get(created.getId(), workspaceId);

    assertThat(fetched.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldThrowWhenGetNotFound() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    assertThatThrownBy(() -> productService.get(UUID.randomUUID(), workspaceId))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenGetWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "wrong-ws", null, walletId, FulfilmentType.INVITE, null, null);

    assertThatThrownBy(() -> productService.get(created.getId(), UUID.randomUUID()))
        .isInstanceOf(ProductNotFoundException.class);

    // row still exists
    assertThat(productRepository.findById(created.getId())).isPresent();
  }
}
