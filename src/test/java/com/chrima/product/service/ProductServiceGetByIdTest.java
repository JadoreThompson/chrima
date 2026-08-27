package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.product.dto.ProductResponse;
import com.chrima.product.exception.ProductNotFoundException;
import com.chrima.product.model.enums.FulfilmentType;
import com.chrima.user.model.User;
import com.chrima.wallet.model.Wallet;
import com.chrima.workspace.model.Workspace;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceGetByIdTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldGetById() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(), "get-by-id", "desc", wallet.getId(), FulfilmentType.INVITE, null, null);

    ProductResponse fetched = productService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getName()).isEqualTo("get-by-id");
    assertThat(fetched.getDescription()).isEqualTo("desc");
    assertThat(fetched.getWorkspaceId()).isEqualTo(ws.getId());
    assertThat(fetched.getWalletId()).isEqualTo(wallet.getId());
    assertThat(fetched.getFulfilmentType()).isEqualTo(FulfilmentType.INVITE);
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> productService.getById(UUID.randomUUID()))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldGetByIdWithRolesAndExternalUrl() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    Wallet wallet = createWallet(ws.getId());
    ProductResponse created =
        productService.create(
            ws.getId(),
            "with-roles",
            null,
            wallet.getId(),
            FulfilmentType.ROLE,
            "https://external.url",
            List.of("r1", "r2"));

    ProductResponse fetched = productService.getById(created.getId());

    assertThat(fetched.getRoles()).containsExactly("r1", "r2");
    assertThat(fetched.getExternalUrl()).isEqualTo("https://external.url");
  }
}
