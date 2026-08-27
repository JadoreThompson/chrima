package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.user.model.User;
import com.chrima.wallet.dto.WalletResponse;
import com.chrima.wallet.model.Wallet;
import com.chrima.workspace.exception.WorkspaceNotFoundException;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceCreateTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldCreateWalletAndPersist() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());

    WalletResponse wallet = walletService.create(ws.getId(), "main-wallet", "0xwallet");

    assertThat(wallet.getId()).isNotNull();
    assertThat(wallet.getName()).isEqualTo("main-wallet");
    assertThat(wallet.getWalletAddress()).isEqualTo("0xwallet");
    assertThat(wallet.getWorkspaceId()).isEqualTo(ws.getId());
    assertThat(wallet.getCreatedAt()).isNotNull();

    Wallet row = walletRepository.findById(wallet.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("main-wallet");
    assertThat(row.getWalletAddress()).isEqualTo("0xwallet");
    assertThat(row.getWorkspaceId()).isEqualTo(ws.getId());
  }

  @Test
  void shouldThrowWhenWorkspaceNotFoundOnCreate() {
    UUID randomWorkspaceId = UUID.randomUUID();

    assertThatThrownBy(() -> walletService.create(randomWorkspaceId, "wallet", "0xwallet"))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }
}
