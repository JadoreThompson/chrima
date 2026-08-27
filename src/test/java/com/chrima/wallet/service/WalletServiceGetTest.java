package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.wallet.api.dto.WalletResponse;
import com.chrima.wallet.exception.WalletNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceGetTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldGet() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    WalletResponse created = walletService.create(workspaceId, "get-wallet", "0xwallet");

    WalletResponse fetched = walletService.get(created.getId(), workspaceId);

    assertThat(fetched.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldThrowWhenGetNotFound() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    assertThatThrownBy(() -> walletService.get(UUID.randomUUID(), workspaceId))
        .isInstanceOf(WalletNotFoundException.class);
  }

  @Test
  void shouldThrowWhenGetWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    WalletResponse created = walletService.create(workspaceId, "wrong-ws", "0xwallet");

    assertThatThrownBy(() -> walletService.get(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WalletNotFoundException.class);

    // row still exists
    assertThat(walletRepository.findById(created.getId())).isPresent();
  }
}
