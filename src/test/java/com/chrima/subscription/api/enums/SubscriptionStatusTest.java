package com.chrima.subscription.api.enums;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import org.junit.jupiter.api.Test;

class SubscriptionStatusTest {

  @Test
  void shouldReturnSerializedValue() {
    assertThat(SubscriptionStatus.ACTIVE.getValue()).isEqualTo("active");
    assertThat(SubscriptionStatus.EXPIRED.getValue()).isEqualTo("expired");
    assertThat(SubscriptionStatus.CANCELLED.getValue()).isEqualTo("cancelled");
    assertThat(SubscriptionStatus.INCOMPLETE.getValue()).isEqualTo("incomplete");
  }

  @Test
  void shouldResolveFromValue() {
    assertThat(SubscriptionStatus.fromValue("active")).isEqualTo(SubscriptionStatus.ACTIVE);
    assertThat(SubscriptionStatus.fromValue("expired")).isEqualTo(SubscriptionStatus.EXPIRED);
    assertThat(SubscriptionStatus.fromValue("cancelled")).isEqualTo(SubscriptionStatus.CANCELLED);
    assertThat(SubscriptionStatus.fromValue("incomplete")).isEqualTo(SubscriptionStatus.INCOMPLETE);
  }

  @Test
  void shouldThrowWhenValueUnknown() {
    assertThatThrownBy(() -> SubscriptionStatus.fromValue("unknown"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unknown SubscriptionStatus value: unknown");
  }
}
