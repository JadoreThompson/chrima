package com.chrima.events.model;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.Map;
import org.junit.jupiter.api.Test;

class EventTopicRegistryTest {

  @Test
  void shouldReturnTopicForKnownEventType() {
    EventTopicRegistry registry =
        new EventTopicRegistry(Map.of("order.created", "orders", "user.registered", "users"));

    assertThat(registry.getTopic("order.created")).isEqualTo("orders");
    assertThat(registry.getTopic("user.registered")).isEqualTo("users");
  }

  @Test
  void shouldThrowWhenEventTypeNotMapped() {
    EventTopicRegistry registry = new EventTopicRegistry(Map.of("order.created", "orders"));

    assertThatThrownBy(() -> registry.getTopic("unknown.event"))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("No topic registered for event type");
  }

  @Test
  void shouldBeImmutableCopy() {
    Map<String, String> mutable = new java.util.HashMap<>();
    mutable.put("k", "v");
    EventTopicRegistry registry = new EventTopicRegistry(mutable);
    mutable.put("k2", "v2");

    assertThat(registry.contains("k2")).isFalse();
  }
}
