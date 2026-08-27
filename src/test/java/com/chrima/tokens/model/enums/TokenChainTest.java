package com.chrima.tokens.model.enums;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class TokenChainTest {

  @Test
  void shouldReturnSerializedValueForEth() {
    assertThat(TokenChain.ETH.getValue()).isEqualTo("ethereum");
  }

  @Test
  void shouldResolveFromValue() {
    assertThat(TokenChain.fromValue("ethereum")).isEqualTo(TokenChain.ETH);
  }

  @Test
  void shouldThrowWhenValueUnknown() {
    assertThatThrownBy(() -> TokenChain.fromValue("arbitrum"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unknown TokenChain value: arbitrum");
  }
}
