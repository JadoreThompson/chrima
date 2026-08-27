package com.chrima.wallet.api.dto;

import com.chrima.wallet.model.Wallet;
import java.time.Instant;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class WalletResponse {
  UUID id;
  UUID workspaceId;
  String name;
  String walletAddress;
  Instant createdAt;

  public static WalletResponse from(Wallet wallet) {
    return WalletResponse.builder()
        .id(wallet.getId())
        .workspaceId(wallet.getWorkspaceId())
        .name(wallet.getName())
        .walletAddress(wallet.getWalletAddress())
        .createdAt(wallet.getCreatedAt())
        .build();
  }
}
