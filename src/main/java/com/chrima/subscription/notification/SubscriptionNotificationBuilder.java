package com.chrima.subscription.notification;

import com.chrima.notification.discord.api.IDiscordNotificationBuilder;
import com.chrima.notification.discord.api.IDiscordNotificationContent;
import java.awt.Color;
import lombok.extern.slf4j.Slf4j;
import net.dv8tion.jda.api.EmbedBuilder;
import net.dv8tion.jda.api.entities.MessageEmbed;
import org.springframework.stereotype.Component;

@Slf4j
@Component
public class SubscriptionNotificationBuilder
    implements IDiscordNotificationBuilder<IDiscordNotificationContent> {

  @Override
  public boolean supports(Class<? extends IDiscordNotificationContent> contentType) {
    return contentType == SubscriptionExpiringNotificationContent.class
        || contentType == SubscriptionExpiredNotificationContent.class;
  }

  @Override
  public MessageEmbed build(IDiscordNotificationContent content) {
    if (content instanceof SubscriptionExpiringNotificationContent expiring) {
      return buildExpiring(expiring);
    }
    if (content instanceof SubscriptionExpiredNotificationContent expired) {
      return buildExpired(expired);
    }
    log.warn(
        "Unsupported Discord notification content type={}", content.getClass().getSimpleName());
    throw new IllegalArgumentException(
        "Unsupported Discord notification content: " + content.getClass().getSimpleName());
  }

  private MessageEmbed buildExpiring(SubscriptionExpiringNotificationContent content) {
    return new EmbedBuilder()
        .setTitle("Subscription Expiring")
        .setDescription("Your subscription is about to expire. Renew to keep access.")
        .setColor(Color.ORANGE)
        .addField("Product", content.productName(), true)
        .addField("Cycle End", String.valueOf(content.cycleEnd()), true)
        .build();
  }

  private MessageEmbed buildExpired(SubscriptionExpiredNotificationContent content) {
    return new EmbedBuilder()
        .setTitle("Subscription Expired")
        .setDescription("Your subscription has expired. Renew to regain access.")
        .setColor(Color.RED)
        .addField("Product", content.productName(), true)
        .addField("Cycle End", String.valueOf(content.cycleEnd()), true)
        .build();
  }
}
