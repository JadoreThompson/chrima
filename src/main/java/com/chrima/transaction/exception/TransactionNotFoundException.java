package com.chrima.transaction.exception;

import java.util.UUID;

public class TransactionNotFoundException extends RuntimeException {

  private final UUID transactionId;

  public TransactionNotFoundException(UUID transactionId) {
    super("Transaction not found");
    this.transactionId = transactionId;
  }

  public UUID getTransactionId() {
    return transactionId;
  }
}
