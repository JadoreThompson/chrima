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

class ProductServiceGetTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldGet() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "get-ws", "desc", wallet.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse fetched = productService.get(created.getId(), ws.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldThrowWhenGetNotFound() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());

    assertThatThrownBy(() -> productService.get(UUID.randomUUID(), ws.getId()))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldThrowWhenGetWrongWorkspace() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "wrong-ws", null, wallet.getId(), FulfilmentType.INVITE, null, null);

    assertThatThrownBy(() -> productService.get(created.getId(), UUID.randomUUID()))
        .isInstanceOf(ProductNotFoundException.class);

    // row still exists
    assertThat(productRepository.findById(created.getId())).isPresent();
  }
}
