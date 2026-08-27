package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.user.model.User;
import com.chrima.wallet.dto.WalletResponse;
import com.chrima.wallet.exception.WalletNotFoundException;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceGetByIdTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldGetById() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    WalletResponse created = walletService.create(ws.getId(), "get-by-id", "0xwallet");

    WalletResponse fetched = walletService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getName()).isEqualTo("get-by-id");
    assertThat(fetched.getWalletAddress()).isEqualTo("0xwallet");
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> walletService.getById(UUID.randomUUID()))
        .isInstanceOf(WalletNotFoundException.class);
  }
}
