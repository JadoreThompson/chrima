package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.product.dto.ProductResponse;
import com.chrima.product.exception.ProductNotFoundException;
import com.chrima.product.model.enums.FulfilmentType;
import com.chrima.user.model.User;
import com.chrima.wallet.model.Wallet;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceDeleteTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldDeleteProductAndVerifyGone() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "to-delete", null, wallet.getId(), FulfilmentType.INVITE, null, null);

    productService.delete(created.getId(), ws.getId());

    assertThat(productRepository.findById(created.getId())).isEmpty();
    assertThatThrownBy(() -> productService.getById(created.getId()))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteNotFound() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());

    assertThatThrownBy(() -> productService.delete(UUID.randomUUID(), ws.getId()))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteWrongWorkspace() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "wrong-ws-del", null, wallet.getId(), FulfilmentType.INVITE, null, null);

    assertThatThrownBy(() -> productService.delete(created.getId(), UUID.randomUUID()))
        .isInstanceOf(ProductNotFoundException.class);

    assertThat(productRepository.findById(created.getId())).isPresent();
  }
}
