package com.chrima.tokens.api.enums;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class TokenStandardTest {

  @Test
  void shouldReturnSerializedValueForErc20() {
    assertThat(TokenStandard.ERC_20.getValue()).isEqualTo("erc-20");
  }

  @Test
  void shouldResolveFromValue() {
    assertThat(TokenStandard.fromValue("erc-20")).isEqualTo(TokenStandard.ERC_20);
  }

  @Test
  void shouldThrowWhenValueUnknown() {
    assertThatThrownBy(() -> TokenStandard.fromValue("bep-20"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unknown TokenStandard value: bep-20");
  }
}
