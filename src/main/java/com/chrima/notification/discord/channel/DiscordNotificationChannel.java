package com.chrima.notification.discord.channel;

import com.chrima.notification.discord.api.IDiscordNotificationBuilder;
import com.chrima.notification.discord.api.IDiscordNotificationContent;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;

import java.util.List;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.entities.Guild;
import net.dv8tion.jda.api.entities.Message;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class DiscordNotificationChannel {

    private final ObjectProvider<JDA> jdaProvider;
    private final List<IDiscordNotificationBuilder> builders;

    @SuppressWarnings("unchecked")
    @WithSpan
    public Long send(
            @SpanAttribute("discord.guild_id") Long guildId,
            @SpanAttribute("discord.channel_id") Long channelId,
            IDiscordNotificationContent content,
            @SpanAttribute("discord.idempotency_key") String idempotencyKey) {
        log.info(
                "Sending Discord message guildId={} channelId={} type={} idempotencyKey={}",
                guildId,
                channelId,
                content.getClass().getSimpleName(),
                idempotencyKey);
        JDA jda = jdaProvider.getIfAvailable();
        if (jda == null) {
            log.error(
                    "Discord bot is not configured - cannot send guildId={} channelId={}",
                    guildId,
                    channelId);
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

        try {
            Message message =
                    textChannel
                            .sendMessageEmbeds(builder.build(content))
                            .setNonce(DiscordNonce.from(idempotencyKey))
                            .complete();
            log.info(
                    "Discord message sent guildId={} channelId={} discordMessageId={} idempotencyKey={}",
                    guildId,
                    channelId,
                    message.getIdLong(),
                    idempotencyKey);
            return message.getIdLong();
        } catch (Exception e) {
            log.error(
                    "Failed to send Discord message guildId={} channelId={} type={} idempotencyKey={}",
                    guildId,
                    channelId,
                    content.getClass().getSimpleName(),
                    idempotencyKey,
                    e);
            throw e;
        }
    }
}
