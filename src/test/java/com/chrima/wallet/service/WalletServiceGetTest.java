package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.user.model.User;
import com.chrima.wallet.dto.WalletResponse;
import com.chrima.wallet.exception.WalletNotFoundException;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceGetTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldGet() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    WalletResponse created = walletService.create(ws.getId(), "get-wallet", "0xwallet");

    WalletResponse fetched = walletService.get(created.getId(), ws.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldThrowWhenGetNotFound() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());

    assertThatThrownBy(() -> walletService.get(UUID.randomUUID(), ws.getId()))
        .isInstanceOf(WalletNotFoundException.class);
  }

  @Test
  void shouldThrowWhenGetWrongWorkspace() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    WalletResponse created = walletService.create(ws.getId(), "wrong-ws", "0xwallet");

    assertThatThrownBy(() -> walletService.get(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WalletNotFoundException.class);

    // row still exists
    assertThat(walletRepository.findById(created.getId())).isPresent();
  }
}
