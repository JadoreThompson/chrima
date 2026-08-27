package com.chrima.price.api.enums;

public enum PriceType {
  ONE_TIME("one_time"),
  RECURRING("recurring");

  private final String value;

  PriceType(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  public static PriceType fromValue(String value) {
    for (PriceType t : values()) {
      if (t.value.equals(value)) {
        return t;
      }
    }
    throw new IllegalArgumentException("Unknown PriceType value: " + value);
  }
}
