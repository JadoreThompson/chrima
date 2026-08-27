package com.chrima.wallet.dto;

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
}
