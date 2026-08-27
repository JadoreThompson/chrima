package com.chrima.wallet.model;

import java.io.Serializable;
import java.util.UUID;
import lombok.AllArgsConstructor;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode
public class WalletTokenId implements Serializable {

  private UUID walletId;
  private UUID tokenId;
}
