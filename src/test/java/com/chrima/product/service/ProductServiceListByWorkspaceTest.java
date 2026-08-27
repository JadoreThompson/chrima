package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.product.dto.ProductResponse;
import com.chrima.product.model.enums.FulfilmentType;
import com.chrima.user.model.User;
import com.chrima.wallet.model.Wallet;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

class ProductServiceListByWorkspaceTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldListByWorkspaceReturnsProducts() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse p1 =
        productService.create(
            ws.getId(), "product-a", null, wallet.getId(), FulfilmentType.INVITE, null, null);
    ProductResponse p2 =
        productService.create(
            ws.getId(), "product-b", null, wallet.getId(), FulfilmentType.ROLE, null, null);

    Page<ProductResponse> result =
        productService.listByWorkspace(ws.getId(), PageRequest.of(0, 10));

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
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    for (int i = 0; i < 3; i++) {
      productService.create(
          ws.getId(), "product-" + i, null, wallet.getId(), FulfilmentType.INVITE, null, null);
    }

    Page<ProductResponse> result = productService.listByWorkspace(ws.getId(), PageRequest.of(0, 2));

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
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    for (int i = 0; i < 3; i++) {
      productService.create(
          ws.getId(), "product", null, wallet.getId(), FulfilmentType.INVITE, null, null);
    }

    Page<ProductResponse> page1 = productService.listByWorkspace(ws.getId(), PageRequest.of(0, 2));
    Page<ProductResponse> page2 = productService.listByWorkspace(ws.getId(), PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  @Test
  void shouldListByWorkspaceIsolatedByWorkspace() {
    User user = createUser();
    Workspace ws1 = createWorkspace(user.getId());
    Workspace ws2 = createWorkspace(user.getId());
    Wallet wallet1 = createWallet(ws1.getId());
    Wallet wallet2 = createWallet(ws2.getId());
    productService.create(
        ws1.getId(), "ws1-product", null, wallet1.getId(), FulfilmentType.INVITE, null, null);
    productService.create(
        ws2.getId(), "ws2-product", null, wallet2.getId(), FulfilmentType.INVITE, null, null);

    Page<ProductResponse> result1 =
        productService.listByWorkspace(ws1.getId(), PageRequest.of(0, 10));
    Page<ProductResponse> result2 =
        productService.listByWorkspace(ws2.getId(), PageRequest.of(0, 10));

    assertThat(result1.getContent()).hasSize(1);
    assertThat(result1.getContent().get(0).getName()).isEqualTo("ws1-product");
    assertThat(result2.getContent()).hasSize(1);
    assertThat(result2.getContent().get(0).getName()).isEqualTo("ws2-product");
  }

  @Test
  void shouldSupportLegacyPageAndLimitOverload() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    for (int i = 0; i < 3; i++) {
      productService.create(
          ws.getId(), "product", null, wallet.getId(), FulfilmentType.INVITE, null, null);
    }

    Page<ProductResponse> page1 = productService.listByWorkspace(ws.getId(), 1, 2);
    Page<ProductResponse> page2 = productService.listByWorkspace(ws.getId(), 2, 2);

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }
}
