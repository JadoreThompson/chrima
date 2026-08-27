package com.chrima.tokens.api.enums;

public enum TokenChain {
  ETH("ethereum");

  private final String value;

  TokenChain(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  public static TokenChain fromValue(String value) {
    for (TokenChain c : values()) {
      if (c.value.equals(value)) {
        return c;
      }
    }
    throw new IllegalArgumentException("Unknown TokenChain value: " + value);
  }
}
