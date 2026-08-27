package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.exception.ProductNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceDeleteTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldDeleteProductAndVerifyGone() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "to-delete", null, walletId, FulfilmentType.INVITE, null, null);

    productService.delete(created.getId(), workspaceId);

    assertThat(productRepository.findById(created.getId())).isEmpty();
    assertThatThrownBy(() -> productService.getById(created.getId()))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteNotFound() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    assertThatThrownBy(() -> productService.delete(UUID.randomUUID(), workspaceId))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "wrong-ws-del", null, walletId, FulfilmentType.INVITE, null, null);

    assertThatThrownBy(() -> productService.delete(created.getId(), UUID.randomUUID()))
        .isInstanceOf(ProductNotFoundException.class);

    assertThat(productRepository.findById(created.getId())).isPresent();
  }
}
