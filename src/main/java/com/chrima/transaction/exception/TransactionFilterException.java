package com.chrima.transaction.exception;

public class TransactionFilterException extends RuntimeException {

  public TransactionFilterException() {
    super("At least one filter parameter is required");
  }
}
