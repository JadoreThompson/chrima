package com.chrima.price.api.enums;

public enum RecurringInterval {
  DAY("day"),
  MONTH("month");

  private final String value;

  RecurringInterval(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  public static RecurringInterval fromValue(String value) {
    for (RecurringInterval i : values()) {
      if (i.value.equals(value)) {
        return i;
      }
    }
    throw new IllegalArgumentException("Unknown RecurringInterval value: " + value);
  }
}
