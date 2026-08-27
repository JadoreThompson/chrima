package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.model.Product;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceCreateTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldCreateProductAndPersist() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());

    ProductResponse product =
        productService.create(
            workspaceId,
            "test-product",
            "description",
            walletId,
            FulfilmentType.INVITE,
            "https://example.com",
            List.of("role1", "role2"));

    assertThat(product.getId()).isNotNull();
    assertThat(product.getName()).isEqualTo("test-product");
    assertThat(product.getDescription()).isEqualTo("description");
    assertThat(product.getWorkspaceId()).isEqualTo(workspaceId);
    assertThat(product.getWalletId()).isEqualTo(walletId);
    assertThat(product.getFulfilmentType()).isEqualTo(FulfilmentType.INVITE);
    assertThat(product.getExternalUrl()).isEqualTo("https://example.com");
    assertThat(product.getRoles()).containsExactly("role1", "role2");
    assertThat(product.getCreatedAt()).isNotNull();
    assertThat(product.getUpdatedAt()).isNotNull();

    Product row = productRepository.findById(product.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("test-product");
    assertThat(row.getDescription()).isEqualTo("description");
    assertThat(row.getWorkspaceId()).isEqualTo(workspaceId);
    assertThat(row.getWalletId()).isEqualTo(walletId);
    assertThat(row.getFulfilmentType()).isEqualTo(FulfilmentType.INVITE);
    assertThat(row.getExternalUrl()).isEqualTo("https://example.com");
    assertThat(row.getRoles()).containsExactly("role1", "role2");
  }

  @Test
  void shouldCreateProductWithMinimalFields() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());

    ProductResponse product =
        productService.create(
            workspaceId, "minimal", null, walletId, FulfilmentType.ROLE, null, null);

    assertThat(product.getId()).isNotNull();
    assertThat(product.getName()).isEqualTo("minimal");
    assertThat(product.getDescription()).isNull();
    assertThat(product.getExternalUrl()).isNull();
    assertThat(product.getRoles()).isNull();
    assertThat(product.getFulfilmentType()).isEqualTo(FulfilmentType.ROLE);
  }

  @Test
  void shouldThrowWhenWorkspaceNotFoundOnCreate() {
    UUID workspaceId = UUID.randomUUID();
    UUID walletId = mockWalletExists(UUID.randomUUID());
    when(workspaceService.getById(any())).thenThrow(new RuntimeException("Workspace not found"));

    assertThatThrownBy(
            () ->
                productService.create(
                    workspaceId, "product", null, walletId, FulfilmentType.INVITE, null, null))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("Workspace not found");
  }

  @Test
  void shouldThrowWhenWalletNotFoundOnCreate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = UUID.randomUUID();
    when(walletService.getById(any())).thenThrow(new RuntimeException("Wallet not found"));

    assertThatThrownBy(
            () ->
                productService.create(
                    workspaceId, "product", null, walletId, FulfilmentType.INVITE, null, null))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("Wallet not found");
  }
}
