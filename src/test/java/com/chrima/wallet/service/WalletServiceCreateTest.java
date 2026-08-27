package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.chrima.wallet.api.dto.WalletResponse;
import com.chrima.wallet.model.Wallet;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceCreateTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldCreateWalletAndPersist() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    WalletResponse wallet = walletService.create(workspaceId, "main-wallet", "0xwallet");

    assertThat(wallet.getId()).isNotNull();
    assertThat(wallet.getName()).isEqualTo("main-wallet");
    assertThat(wallet.getWalletAddress()).isEqualTo("0xwallet");
    assertThat(wallet.getWorkspaceId()).isEqualTo(workspaceId);
    assertThat(wallet.getCreatedAt()).isNotNull();

    Wallet row = walletRepository.findById(wallet.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("main-wallet");
    assertThat(row.getWalletAddress()).isEqualTo("0xwallet");
    assertThat(row.getWorkspaceId()).isEqualTo(workspaceId);
  }

  @Test
  void shouldThrowWhenWorkspaceNotFoundOnCreate() {
    UUID randomWorkspaceId = UUID.randomUUID();
    when(workspaceService.getById(any())).thenThrow(new RuntimeException("Workspace not found"));

    assertThatThrownBy(() -> walletService.create(randomWorkspaceId, "wallet", "0xwallet"))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("Workspace not found");
  }
}
