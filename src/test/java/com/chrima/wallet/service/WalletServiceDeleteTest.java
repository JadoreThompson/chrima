package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.user.model.User;
import com.chrima.wallet.dto.WalletResponse;
import com.chrima.wallet.exception.WalletNotFoundException;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceDeleteTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldDeleteWalletAndVerifyGone() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    WalletResponse created = walletService.create(ws.getId(), "to-delete", "0xwallet");

    walletService.delete(created.getId(), ws.getId());

    assertThat(walletRepository.findById(created.getId())).isEmpty();
    assertThatThrownBy(() -> walletService.getById(created.getId()))
        .isInstanceOf(WalletNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteNotFound() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());

    assertThatThrownBy(() -> walletService.delete(UUID.randomUUID(), ws.getId()))
        .isInstanceOf(WalletNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteWrongWorkspace() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    WalletResponse created = walletService.create(ws.getId(), "wrong-ws-del", "0xwallet");

    assertThatThrownBy(() -> walletService.delete(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WalletNotFoundException.class);

    assertThat(walletRepository.findById(created.getId())).isPresent();
  }
}
