package com.chrima.notification.discord.api;

import net.dv8tion.jda.api.entities.MessageEmbed;

public interface IDiscordNotificationBuilder<T extends IDiscordNotificationContent> {

  boolean supports(Class<? extends IDiscordNotificationContent> contentType);

  MessageEmbed build(T content);
}
