package com.chrima.subscription.notification;

import com.chrima.notification.discord.api.DiscordNotificationType;
import com.chrima.notification.discord.api.IDiscordNotificationContent;
import java.util.UUID;

@DiscordNotificationType(SubscriptionExpiredNotificationContent.TYPE)
public record SubscriptionExpiredNotificationContent(
    String guildId,
    String channelId,
    String platformUserId,
    UUID productId,
    String productName,
    long cycleEnd)
    implements IDiscordNotificationContent {

  public static final String TYPE = "subscription.expired";
}
