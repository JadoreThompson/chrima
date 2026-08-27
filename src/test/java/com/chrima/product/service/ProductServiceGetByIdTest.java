package com.chrima.product.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.product.api.dto.ProductResponse;
import com.chrima.product.api.enums.FulfilmentType;
import com.chrima.product.exception.ProductNotFoundException;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class ProductServiceGetByIdTest extends AbstractProductServiceIntegrationBase {

  @Test
  void shouldGetById() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId, "get-by-id", "desc", walletId, FulfilmentType.INVITE, null, null);

    ProductResponse fetched = productService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getName()).isEqualTo("get-by-id");
    assertThat(fetched.getDescription()).isEqualTo("desc");
    assertThat(fetched.getWorkspaceId()).isEqualTo(workspaceId);
    assertThat(fetched.getWalletId()).isEqualTo(walletId);
    assertThat(fetched.getFulfilmentType()).isEqualTo(FulfilmentType.INVITE);
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> productService.getById(UUID.randomUUID()))
        .isInstanceOf(ProductNotFoundException.class);
  }

  @Test
  void shouldGetByIdWithRolesAndExternalUrl() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    UUID walletId = mockWalletExists(UUID.randomUUID());
    ProductResponse created =
        productService.create(
            workspaceId,
            "with-roles",
            null,
            walletId,
            FulfilmentType.ROLE,
            "https://external.url",
            List.of("r1", "r2"));

    ProductResponse fetched = productService.getById(created.getId());

    assertThat(fetched.getRoles()).containsExactly("r1", "r2");
    assertThat(fetched.getExternalUrl()).isEqualTo("https://external.url");
  }
}
