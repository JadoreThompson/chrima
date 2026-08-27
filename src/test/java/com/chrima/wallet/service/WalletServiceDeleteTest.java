package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.wallet.api.dto.WalletResponse;
import com.chrima.wallet.exception.WalletNotFoundException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceDeleteTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldDeleteWalletAndVerifyGone() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    WalletResponse created = walletService.create(workspaceId, "to-delete", "0xwallet");

    walletService.delete(created.getId(), workspaceId);

    assertThat(walletRepository.findById(created.getId())).isEmpty();
    assertThatThrownBy(() -> walletService.getById(created.getId()))
        .isInstanceOf(WalletNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteNotFound() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());

    assertThatThrownBy(() -> walletService.delete(UUID.randomUUID(), workspaceId))
        .isInstanceOf(WalletNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteWrongWorkspace() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    WalletResponse created = walletService.create(workspaceId, "wrong-ws-del", "0xwallet");

    assertThatThrownBy(() -> walletService.delete(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WalletNotFoundException.class);

    assertThat(walletRepository.findById(created.getId())).isPresent();
  }
}
