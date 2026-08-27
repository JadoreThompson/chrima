package com.chrima.price.api.enums;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class RecurringIntervalTest {

  @Test
  void shouldReturnSerializedValues() {
    assertThat(RecurringInterval.DAY.getValue()).isEqualTo("day");
    assertThat(RecurringInterval.MONTH.getValue()).isEqualTo("month");
  }

  @Test
  void shouldResolveFromValue() {
    assertThat(RecurringInterval.fromValue("day")).isEqualTo(RecurringInterval.DAY);
    assertThat(RecurringInterval.fromValue("month")).isEqualTo(RecurringInterval.MONTH);
  }

  @Test
  void shouldThrowWhenValueUnknown() {
    assertThatThrownBy(() -> RecurringInterval.fromValue("year"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unknown RecurringInterval value: year");
  }
}
