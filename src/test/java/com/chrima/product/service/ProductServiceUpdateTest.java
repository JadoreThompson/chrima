package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.product.dto.ProductResponse;
import com.chrima.product.exception.ProductNotFoundException;
import com.chrima.product.model.Product;
import com.chrima.product.model.enums.FulfilmentType;
import com.chrima.user.model.User;
import com.chrima.wallet.exception.WalletNotFoundException;
import com.chrima.wallet.model.Wallet;
import com.chrima.workspace.model.Workspace;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceUpdateTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldUpdateName() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "original", null, wallet.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), ws.getId(), "updated-name", null, null, null, null);

    assertThat(updated.getName()).isEqualTo("updated-name");
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("updated-name");
  }

  @Test
  void shouldUpdateDescription() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "prod", "old-desc", wallet.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), ws.getId(), null, "new-desc", null, null, null);

    assertThat(updated.getDescription()).isEqualTo("new-desc");
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getDescription()).isEqualTo("new-desc");
  }

  @Test
  void shouldUpdateWalletId() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet1 = createWallet(ws.getId(), "w1", "0x1");
    Wallet wallet2 = createWallet(ws.getId(), "w2", "0x2");
    ProductResponse created =
        productService.create(
            ws.getId(), "prod", null, wallet1.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), ws.getId(), null, null, wallet2.getId(), null, null);

    assertThat(updated.getWalletId()).isEqualTo(wallet2.getId());
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getWalletId()).isEqualTo(wallet2.getId());
  }

  @Test
  void shouldUpdateRolesAndExternalUrl() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "prod", null, wallet.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(
            created.getId(), ws.getId(), null, null, null, List.of("new-role"), "https://new.url");

    assertThat(updated.getRoles()).containsExactly("new-role");
    assertThat(updated.getExternalUrl()).isEqualTo("https://new.url");
    Product row = productRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getRoles()).containsExactly("new-role");
    assertThat(row.getExternalUrl()).isEqualTo("https://new.url");
  }

  @Test
  void shouldUpdateWithAllFields() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet1 = createWallet(ws.getId(), "w1", "0x1");
    Wallet wallet2 = createWallet(ws.getId(), "w2", "0x2");
    ProductResponse created =
        productService.create(
            ws.getId(), "orig", "orig-desc", wallet1.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(
            created.getId(),
            ws.getId(),
            "new-name",
            "new-desc",
            wallet2.getId(),
            List.of("r1"),
            "https://url");

    assertThat(updated.getName()).isEqualTo("new-name");
    assertThat(updated.getDescription()).isEqualTo("new-desc");
    assertThat(updated.getWalletId()).isEqualTo(wallet2.getId());
    assertThat(updated.getRoles()).containsExactly("r1");
    assertThat(updated.getExternalUrl()).isEqualTo("https://url");
  }

  @Test
  void shouldThrowWhenUpdateProductNotFound() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());

    assertThatThrownBy(
            () -> productService.update(UUID.randomUUID(), ws.getId(), "x", null, null, null, null))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenUpdateWrongWorkspace() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "prod", null, wallet.getId(), FulfilmentType.INVITE, null, null);

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
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "prod", null, wallet.getId(), FulfilmentType.INVITE, null, null);

    assertThatThrownBy(
            () ->
                productService.update(
                    created.getId(), ws.getId(), null, null, UUID.randomUUID(), null, null))
        .isInstanceOf(WalletNotFoundException.class);
  }

  @Test
  void shouldNotUpdateWhenSameWalletId() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "prod", null, wallet.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse updated =
        productService.update(created.getId(), ws.getId(), null, null, wallet.getId(), null, null);

    assertThat(updated.getWalletId()).isEqualTo(wallet.getId());
  }
}
