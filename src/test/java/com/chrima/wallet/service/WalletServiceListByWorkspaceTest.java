package com.chrima.wallet.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.wallet.api.dto.WalletResponse;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

class WalletServiceListByWorkspaceTest extends AbstractWalletServiceIntegrationBase {

  @Test
  void shouldListByWorkspaceReturnsWallets() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    WalletResponse w1 = walletService.create(workspaceId, "wallet-a", "0xa");
    WalletResponse w2 = walletService.create(workspaceId, "wallet-b", "0xb");

    Page<WalletResponse> result = walletService.listByWorkspace(workspaceId, PageRequest.of(0, 10));

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
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      walletService.create(workspaceId, "wallet", "0xw" + i);
    }

    Page<WalletResponse> result = walletService.listByWorkspace(workspaceId, PageRequest.of(0, 2));

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
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      walletService.create(workspaceId, "wallet", "0xw" + i);
    }

    Page<WalletResponse> page1 = walletService.listByWorkspace(workspaceId, PageRequest.of(0, 2));
    Page<WalletResponse> page2 = walletService.listByWorkspace(workspaceId, PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  @Test
  void shouldListByWorkspaceIsolatedByWorkspace() {
    UUID workspaceId1 = mockWorkspaceExists(UUID.randomUUID());
    UUID workspaceId2 = mockWorkspaceExists(UUID.randomUUID());
    walletService.create(workspaceId1, "ws1-wallet", "0x1");
    walletService.create(workspaceId2, "ws2-wallet", "0x2");

    Page<WalletResponse> result1 =
        walletService.listByWorkspace(workspaceId1, PageRequest.of(0, 10));
    Page<WalletResponse> result2 =
        walletService.listByWorkspace(workspaceId2, PageRequest.of(0, 10));

    assertThat(result1.getContent()).hasSize(1);
    assertThat(result1.getContent().get(0).getName()).isEqualTo("ws1-wallet");
    assertThat(result2.getContent()).hasSize(1);
    assertThat(result2.getContent().get(0).getName()).isEqualTo("ws2-wallet");
  }

  @Test
  void shouldSupportLegacyPageAndLimitOverload() {
    UUID workspaceId = mockWorkspaceExists(UUID.randomUUID());
    for (int i = 0; i < 3; i++) {
      walletService.create(workspaceId, "wallet", "0xw" + i);
    }

    Page<WalletResponse> page1 = walletService.listByWorkspace(workspaceId, 1, 2);
    Page<WalletResponse> page2 = walletService.listByWorkspace(workspaceId, 2, 2);

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }
}
