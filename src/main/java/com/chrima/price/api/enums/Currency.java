package com.chrima.price.api.enums;

public enum Currency {
  USD("usd");

  private final String value;

  Currency(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  public static Currency fromValue(String value) {
    for (Currency c : values()) {
      if (c.value.equals(value)) {
        return c;
      }
    }
    throw new IllegalArgumentException("Unknown Currency value: " + value);
  }
}
