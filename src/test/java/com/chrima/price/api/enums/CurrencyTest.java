package com.chrima.price.api.enums;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class CurrencyTest {

  @Test
  void shouldReturnSerializedValueForUsd() {
    assertThat(Currency.USD.getValue()).isEqualTo("usd");
  }

  @Test
  void shouldResolveFromValue() {
    assertThat(Currency.fromValue("usd")).isEqualTo(Currency.USD);
  }

  @Test
  void shouldThrowWhenValueUnknown() {
    assertThatThrownBy(() -> Currency.fromValue("eur"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unknown Currency value: eur");
  }
}
