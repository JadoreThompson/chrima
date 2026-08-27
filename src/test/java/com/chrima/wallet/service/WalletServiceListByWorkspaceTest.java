package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.user.model.User;
import com.chrima.wallet.dto.WalletResponse;
import com.chrima.workspace.model.Workspace;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

class WalletServiceListByWorkspaceTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldListByWorkspaceReturnsWallets() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    WalletResponse w1 = walletService.create(ws.getId(), "wallet-a", "0xa");
    WalletResponse w2 = walletService.create(ws.getId(), "wallet-b", "0xb");

    Page<WalletResponse> result = walletService.listByWorkspace(ws.getId(), PageRequest.of(0, 10));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.getContent())
        .extracting(WalletResponse::getId)
        .containsExactlyInAnyOrder(w1.getId(), w2.getId());
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getNumber()).isEqualTo(0);
    assertThat(result.getTotalElements()).isEqualTo(2);
  }

  @Test
  void shouldPaginate() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    for (int i = 0; i < 3; i++) {
      walletService.create(ws.getId(), "wallet", "0xw" + i);
    }

    Page<WalletResponse> result = walletService.listByWorkspace(ws.getId(), PageRequest.of(0, 2));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.hasNext()).isTrue();
    assertThat(result.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldReturnEmptyWhenNoWallets() {
    Page<WalletResponse> result =
        walletService.listByWorkspace(UUID.randomUUID(), PageRequest.of(0, 10));

    assertThat(result.getContent()).isEmpty();
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getTotalElements()).isEqualTo(0);
  }

  @Test
  void shouldPaginateSecondPage() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    for (int i = 0; i < 3; i++) {
      walletService.create(ws.getId(), "wallet", "0xw" + i);
    }

    Page<WalletResponse> page1 = walletService.listByWorkspace(ws.getId(), PageRequest.of(0, 2));
    Page<WalletResponse> page2 = walletService.listByWorkspace(ws.getId(), PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  @Test
  void shouldListByWorkspaceIsolatedByWorkspace() {
    User user = createUser();
    Workspace ws1 = createWorkspace(user.getId());
    Workspace ws2 = createWorkspace(user.getId());
    walletService.create(ws1.getId(), "ws1-wallet", "0x1");
    walletService.create(ws2.getId(), "ws2-wallet", "0x2");

    Page<WalletResponse> result1 =
        walletService.listByWorkspace(ws1.getId(), PageRequest.of(0, 10));
    Page<WalletResponse> result2 =
        walletService.listByWorkspace(ws2.getId(), PageRequest.of(0, 10));

    assertThat(result1.getContent()).hasSize(1);
    assertThat(result1.getContent().get(0).getName()).isEqualTo("ws1-wallet");
    assertThat(result2.getContent()).hasSize(1);
    assertThat(result2.getContent().get(0).getName()).isEqualTo("ws2-wallet");
  }

  @Test
  void shouldSupportLegacyPageAndLimitOverload() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    for (int i = 0; i < 3; i++) {
      walletService.create(ws.getId(), "wallet", "0xw" + i);
    }

    Page<WalletResponse> page1 = walletService.listByWorkspace(ws.getId(), 1, 2);
    Page<WalletResponse> page2 = walletService.listByWorkspace(ws.getId(), 2, 2);

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }
}
