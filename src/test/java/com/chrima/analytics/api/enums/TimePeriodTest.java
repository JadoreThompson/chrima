package com.chrima.analytics.api.enums;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class TimePeriodTest {

  @Test
  void shouldHaveCorrectValues() {
    assertThat(TimePeriod.TODAY.getValue()).isEqualTo("today");
    assertThat(TimePeriod.THIS_WEEK.getValue()).isEqualTo("this_week");
    assertThat(TimePeriod.THIS_MONTH.getValue()).isEqualTo("this_month");
  }

  @Test
  void shouldParseLowercaseValue() {
    assertThat(TimePeriod.fromValue("today")).isEqualTo(TimePeriod.TODAY);
    assertThat(TimePeriod.fromValue("this_week")).isEqualTo(TimePeriod.THIS_WEEK);
    assertThat(TimePeriod.fromValue("this_month")).isEqualTo(TimePeriod.THIS_MONTH);
  }

  @Test
  void shouldParseCaseInsensitiveName() {
    assertThat(TimePeriod.fromValue("TODAY")).isEqualTo(TimePeriod.TODAY);
    assertThat(TimePeriod.fromValue("THIS_WEEK")).isEqualTo(TimePeriod.THIS_WEEK);
    assertThat(TimePeriod.fromValue("This_Month")).isEqualTo(TimePeriod.THIS_MONTH);
  }

  @Test
  void shouldThrowOnUnknownValue() {
    assertThatThrownBy(() -> TimePeriod.fromValue("unknown"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unknown TimePeriod");
  }

  @Test
  void shouldThrowOnNullValue() {
    assertThatThrownBy(() -> TimePeriod.fromValue(null)).isInstanceOf(Exception.class);
  }

  @Test
  void shouldHaveThreeValues() {
    assertThat(TimePeriod.values()).hasSize(3);
  }
}
