package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.product.dto.ProductResponse;
import com.chrima.product.model.Product;
import com.chrima.product.model.enums.FulfilmentType;
import com.chrima.user.model.User;
import com.chrima.wallet.exception.WalletNotFoundException;
import com.chrima.wallet.model.Wallet;
import com.chrima.workspace.exception.WorkspaceNotFoundException;
import com.chrima.workspace.model.Workspace;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceCreateTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldCreateProductAndPersist() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());

    ProductResponse product =
        productService.create(
            ws.getId(),
            "test-product",
            "description",
            wallet.getId(),
            FulfilmentType.INVITE,
            "https://example.com",
            List.of("role1", "role2"));

    assertThat(product.getId()).isNotNull();
    assertThat(product.getName()).isEqualTo("test-product");
    assertThat(product.getDescription()).isEqualTo("description");
    assertThat(product.getWorkspaceId()).isEqualTo(ws.getId());
    assertThat(product.getWalletId()).isEqualTo(wallet.getId());
    assertThat(product.getFulfilmentType()).isEqualTo(FulfilmentType.INVITE);
    assertThat(product.getExternalUrl()).isEqualTo("https://example.com");
    assertThat(product.getRoles()).containsExactly("role1", "role2");
    assertThat(product.getCreatedAt()).isNotNull();
    assertThat(product.getUpdatedAt()).isNotNull();

    Product row = productRepository.findById(product.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("test-product");
    assertThat(row.getDescription()).isEqualTo("description");
    assertThat(row.getWorkspaceId()).isEqualTo(ws.getId());
    assertThat(row.getWalletId()).isEqualTo(wallet.getId());
    assertThat(row.getFulfilmentType()).isEqualTo(FulfilmentType.INVITE);
    assertThat(row.getExternalUrl()).isEqualTo("https://example.com");
    assertThat(row.getRoles()).containsExactly("role1", "role2");
  }

  @Test
  void shouldCreateProductWithMinimalFields() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());

    ProductResponse product =
        productService.create(
            ws.getId(), "minimal", null, wallet.getId(), FulfilmentType.ROLE, null, null);

    assertThat(product.getId()).isNotNull();
    assertThat(product.getName()).isEqualTo("minimal");
    assertThat(product.getDescription()).isNull();
    assertThat(product.getExternalUrl()).isNull();
    assertThat(product.getRoles()).isNull();
    assertThat(product.getFulfilmentType()).isEqualTo(FulfilmentType.ROLE);
  }

  @Test
  void shouldThrowWhenWorkspaceNotFoundOnCreate() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    UUID randomWorkspaceId = UUID.randomUUID();

    assertThatThrownBy(
            () ->
                productService.create(
                    randomWorkspaceId,
                    "product",
                    null,
                    wallet.getId(),
                    FulfilmentType.INVITE,
                    null,
                    null))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenWalletNotFoundOnCreate() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    UUID randomWalletId = UUID.randomUUID();

    assertThatThrownBy(
            () ->
                productService.create(
                    ws.getId(), "product", null, randomWalletId, FulfilmentType.INVITE, null, null))
        .isInstanceOf(WalletNotFoundException.class);
  }
}
