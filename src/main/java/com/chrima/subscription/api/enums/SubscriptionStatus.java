package com.chrima.subscription.api.enums;

public enum SubscriptionStatus {
  ACTIVE("active"),
  EXPIRED("expired"),
  CANCELLED("cancelled"),
  /** The subscription requires more amount from the customer. */
  INCOMPLETE("incomplete");

  private final String value;

  SubscriptionStatus(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  public static SubscriptionStatus fromValue(String value) {
    for (SubscriptionStatus status : values()) {
      if (status.value.equals(value)) {
        return status;
      }
    }
    throw new IllegalArgumentException("Unknown SubscriptionStatus value: " + value);
  }
}
