package com.chrima.wallet.dto;

import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class CreateWalletRequest {
  UUID workspaceId;
  String name;
  String walletAddress;
}
