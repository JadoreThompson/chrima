package com.chrima.wallet.dto;

import com.chrima.wallet.model.Wallet;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class CreateWalletRequest {
  UUID workspaceId;
  String name;
  String walletAddress;

  public static CreateWalletRequest from(Wallet wallet) {
    return CreateWalletRequest.builder()
        .workspaceId(wallet.getWorkspaceId())
        .name(wallet.getName())
        .walletAddress(wallet.getWalletAddress())
        .build();
  }
}
