package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.user.model.User;
import com.chrima.wallet.dto.PaginatedWalletResponse;
import com.chrima.wallet.dto.WalletResponse;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class WalletServiceListByWorkspaceTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldListByWorkspaceReturnsWallets() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    WalletResponse w1 = walletService.create(ws.getId(), "wallet-a", "0xa");
    WalletResponse w2 = walletService.create(ws.getId(), "wallet-b", "0xb");

    PaginatedWalletResponse result = walletService.listByWorkspace(ws.getId(), 1, 10);

    assertThat(result.getSize()).isEqualTo(2);
    assertThat(result.getData())
        .extracting(WalletResponse::getId)
        .containsExactlyInAnyOrder(w1.getId(), w2.getId());
    assertThat(result.isHasNext()).isFalse();
    assertThat(result.getPage()).isEqualTo(1);
  }

  @Test
  void shouldPaginate() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    for (int i = 0; i < 3; i++) {
      walletService.create(ws.getId(), "wallet", "0xw" + i);
    }

    PaginatedWalletResponse result = walletService.listByWorkspace(ws.getId(), 1, 2);

    assertThat(result.getSize()).isEqualTo(2);
    assertThat(result.isHasNext()).isTrue();
  }

  @Test
  void shouldReturnEmptyWhenNoWallets() {
    PaginatedWalletResponse result = walletService.listByWorkspace(UUID.randomUUID(), 1, 10);

    assertThat(result.getSize()).isEqualTo(0);
    assertThat(result.getData()).isEmpty();
    assertThat(result.isHasNext()).isFalse();
  }

  @Test
  void shouldPaginateSecondPage() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    for (int i = 0; i < 3; i++) {
      walletService.create(ws.getId(), "wallet", "0xw" + i);
    }

    PaginatedWalletResponse page1 = walletService.listByWorkspace(ws.getId(), 1, 2);
    PaginatedWalletResponse page2 = walletService.listByWorkspace(ws.getId(), 2, 2);

    assertThat(page1.getSize()).isEqualTo(2);
    assertThat(page1.isHasNext()).isTrue();
    assertThat(page2.getSize()).isEqualTo(1);
    assertThat(page2.isHasNext()).isFalse();
  }

  @Test
  void shouldListByWorkspaceIsolatedByWorkspace() {
    User user = createUser();
    Workspace ws1 = createWorkspace(user.getId());
    Workspace ws2 = createWorkspace(user.getId());
    walletService.create(ws1.getId(), "ws1-wallet", "0x1");
    walletService.create(ws2.getId(), "ws2-wallet", "0x2");

    PaginatedWalletResponse result1 = walletService.listByWorkspace(ws1.getId(), 1, 10);
    PaginatedWalletResponse result2 = walletService.listByWorkspace(ws2.getId(), 1, 10);

    assertThat(result1.getSize()).isEqualTo(1);
    assertThat(result1.getData().get(0).getName()).isEqualTo("ws1-wallet");
    assertThat(result2.getSize()).isEqualTo(1);
    assertThat(result2.getData().get(0).getName()).isEqualTo("ws2-wallet");
  }
}
