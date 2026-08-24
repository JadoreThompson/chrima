package com.chrima.notification.discord.channel;

import com.chrima.notification.discord.api.IDiscordNotificationBuilder;
import com.chrima.notification.discord.api.IDiscordNotificationContent;
import java.util.List;
import lombok.RequiredArgsConstructor;
import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Message;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class DiscordNotificationChannel {

  private final ObjectProvider<JDA> jdaProvider;
  private final List<IDiscordNotificationBuilder> builders;

  @SuppressWarnings("unchecked")
  public Long send(
      Long guildId, Long channelId, IDiscordNotificationContent content, String idempotencyKey) {
    JDA jda = jdaProvider.getIfAvailable();
    if (jda == null) {
      throw new IllegalStateException("Discord bot is not configured");
    }

    IDiscordNotificationBuilder builder =
        builders.stream()
            .filter(candidate -> candidate.supports(content.getClass()))
            .findFirst()
            .orElseThrow(
                () ->
                    new IllegalArgumentException(
                        "No Discord notification builder for type "
                            + content.getClass().getSimpleName()));

    Guild guild = jda.getGuildById(guildId);
    if (guild == null) {
      throw new IllegalArgumentException("Discord guild not found: " + guildId);
    }

    TextChannel textChannel = guild.getTextChannelById(channelId);
    if (textChannel == null) {
      throw new IllegalArgumentException("Discord text channel not found: " + channelId);
    }

    Message message =
        textChannel
            .sendMessageEmbeds(builder.build(content))
            .setNonce(DiscordNonce.from(idempotencyKey))
            .complete();
    return message.getIdLong();
  }
}
