package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.exception.ProductNotFoundException;
import com.chrima.product.model.Product;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceUpdateTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldUpdateName() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "original", null, walletId, FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), workspaceId, "updated-name", null, null, null, null);

    assertThat(updated.getName()).isEqualTo("updated-name");
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("updated-name");
  }

  @Test
  void shouldUpdateDescription() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "prod", "old-desc", walletId, FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), workspaceId, null, "new-desc", null, null, null);

    assertThat(updated.getDescription()).isEqualTo("new-desc");
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getDescription()).isEqualTo("new-desc");
  }

  @Test
  void shouldUpdateWalletId() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID wallet1 = mockWalletExists(UUID.randomUUID());
    UUID wallet2 = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "prod", null, wallet1, FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), workspaceId, null, null, wallet2, null, null);

    assertThat(updated.getWalletId()).isEqualTo(wallet2);
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getWalletId()).isEqualTo(wallet2);
  }

  @Test
  void shouldUpdateRolesAndExternalUrl() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "prod", null, walletId, FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(
            created.getId(), workspaceId, null, null, null, List.of("new-role"), "https://new.url");

    assertThat(updated.getRoles()).containsExactly("new-role");
    assertThat(updated.getExternalUrl()).isEqualTo("https://new.url");
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getRoles()).containsExactly("new-role");
    assertThat(row.getExternalUrl()).isEqualTo("https://new.url");
  }

  @Test
  void shouldUpdateWithAllFields() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID wallet1 = mockWalletExists(UUID.randomUUID());
    UUID wallet2 = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "orig", "orig-desc", wallet1, FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(
            created.getId(),
            workspaceId,
            "new-name",
            "new-desc",
            wallet2,
            List.of("r1"),
            "https://url");

    assertThat(updated.getName()).isEqualTo("new-name");
    assertThat(updated.getDescription()).isEqualTo("new-desc");
    assertThat(updated.getWalletId()).isEqualTo(wallet2);
    assertThat(updated.getRoles()).containsExactly("r1");
    assertThat(updated.getExternalUrl()).isEqualTo("https://url");
  }

  @Test
  void shouldThrowWhenUpdateProductNotFound() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    assertThatThrownBy(
            () ->
                productService.update(UUID.randomUUID(), workspaceId, "x", null, null, null, null))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenUpdateWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "prod", null, walletId, FulfilmentType.INVITE, null, null);

    assertThatThrownBy(
            () ->
                productService.update(
                    created.getId(), UUID.randomUUID(), "x", null, null, null, null))
        .isInstanceOf(ProductNotFoundException.class);

    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("prod");
  }

  @Test
  void shouldThrowWhenWalletNotFoundOnUpdate() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "prod", null, walletId, FulfilmentType.INVITE, null, null);
    when(walletService.getById(any())).thenThrow(new RuntimeException("Wallet not found"));

    assertThatThrownBy(
            () ->
                productService.update(
                    created.getId(), workspaceId, null, null, UUID.randomUUID(), null, null))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("Wallet not found");
  }

  @Test
  void shouldNotUpdateWhenSameWalletId() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "prod", null, walletId, FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), workspaceId, null, null, walletId, null, null);

    assertThat(updated.getWalletId()).isEqualTo(walletId);
  }
}
