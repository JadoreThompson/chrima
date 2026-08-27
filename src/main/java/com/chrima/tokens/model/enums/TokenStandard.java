package com.chrima.tokens.model.enums;

public enum TokenStandard {
  ERC_20("erc-20");

  private final String value;

  TokenStandard(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  public static TokenStandard fromValue(String value) {
    for (TokenStandard s : values()) {
      if (s.value.equals(value)) {
        return s;
      }
    }
    throw new IllegalArgumentException("Unknown TokenStandard value: " + value);
  }
}
