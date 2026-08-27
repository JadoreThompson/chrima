package com.chrima.wallet.exception;

import java.util.UUID;

public class WalletInUseException extends RuntimeException {

  private final UUID walletId;

  public WalletInUseException(UUID walletId) {
    super("Wallet is in use by one or more products and cannot be deleted");
    this.walletId = walletId;
  }

  public UUID getWalletId() {
    return walletId;
  }
}
