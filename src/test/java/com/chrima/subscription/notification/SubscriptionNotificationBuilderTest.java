package com.chrima.subscription.notification;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.UUID;
import net.dv8tion.jda.api.entities.MessageEmbed;
import org.junit.jupiter.api.Test;

class SubscriptionNotificationBuilderTest {

  private final SubscriptionNotificationBuilder builder = new SubscriptionNotificationBuilder();

  @Test
  void shouldSupportExpiringAndExpiredContent() {
    assertThat(builder.supports(SubscriptionExpiringNotificationContent.class)).isTrue();
    assertThat(builder.supports(SubscriptionExpiredNotificationContent.class)).isTrue();
    assertThat(builder.supports(SomeOtherContent.class)).isFalse();
  }

  @Test
  void shouldBuildEmbedForExpiringContent() {
    MessageEmbed embed =
        builder.build(
            new SubscriptionExpiringNotificationContent(
                "12345", "67890", "user-1", UUID.randomUUID(), "Pro", 1234567890L));

    assertThat(embed.getTitle()).isEqualTo("Subscription Expiring");
    assertThat(embed.getFields()).hasSize(2);
  }

  @Test
  void shouldBuildEmbedForExpiredContent() {
    MessageEmbed embed =
        builder.build(
            new SubscriptionExpiredNotificationContent(
                "12345", "67890", "user-1", UUID.randomUUID(), "Pro", 1234567890L));

    assertThat(embed.getTitle()).isEqualTo("Subscription Expired");
    assertThat(embed.getFields()).hasSize(2);
  }

  @Test
  void shouldThrowWhenContentUnsupported() {
    assertThatThrownBy(() -> builder.build(new SomeOtherContent()))
        .isInstanceOf(IllegalArgumentException.class)
        .hasMessageContaining("Unsupported Discord notification content");
  }

  static class SomeOtherContent
      implements com.chrima.notification.discord.api.IDiscordNotificationContent {}
}
