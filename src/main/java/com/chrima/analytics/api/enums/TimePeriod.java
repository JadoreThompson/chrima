package com.chrima.analytics.api.enums;

public enum TimePeriod {
  TODAY("today"),
  THIS_WEEK("this_week"),
  THIS_MONTH("this_month");

  private final String value;

  TimePeriod(String value) {
    this.value = value;
  }

  public String getValue() {
    return value;
  }

  /**
   * Parses a raw string value (case-insensitive) into a {@link TimePeriod}.
   *
   * @param value raw query param value, e.g. "today" or "THIS_WEEK"
   * @return the matching period
   * @throws IllegalArgumentException if no match is found
   */
  public static TimePeriod fromValue(String value) {
    for (TimePeriod period : values()) {
      if (period.value.equalsIgnoreCase(value) || period.name().equalsIgnoreCase(value)) {
        return period;
      }
    }
    throw new IllegalArgumentException("Unknown TimePeriod value: " + value);
  }
}
