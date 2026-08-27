package com.chrima.price.api.enums;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class PriceTypeTest {

  @Test
  void shouldReturnSerializedValues() {
    assertThat(PriceType.ONE_TIME.getValue()).isEqualTo("one_time");
    assertThat(PriceType.RECURRING.getValue()).isEqualTo("recurring");
  }

  @Test
  void shouldResolveFromValue() {
    assertThat(PriceType.fromValue("one_time")).isEqualTo(PriceType.ONE_TIME);
    assertThat(PriceType.fromValue("recurring")).isEqualTo(PriceType.RECURRING);
  }

  @Test
  void shouldThrowWhenValueUnknown() {
    assertThatThrownBy(() -> PriceType.fromValue("lifetime"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unknown PriceType value: lifetime");
  }
}
