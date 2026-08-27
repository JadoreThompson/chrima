package com.chrima.transaction.api.enums;

public enum TransactionStatus {
  COMPLETE("complete"),
  FAILED("failed");

  private final String value;

  TransactionStatus(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  public static TransactionStatus fromValue(String value) {
    for (TransactionStatus status : values()) {
      if (status.value.equals(value)) {
        return status;
      }
    }
    throw new IllegalArgumentException("Unknown TransactionStatus value: " + value);
  }
}
