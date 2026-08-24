package com.chrima.notification.discord.api;

public interface IDiscordNotificationService {

  void publish(
      Long guildId,
      Long channelId,
      String type,
      IDiscordNotificationContent content,
      String idempotencyKey);
}
