package com.chrima.notification.discord.service;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.api.IDiscordNotificationService;
import com.chrima.notification.discord.model.DiscordNotification;
import com.chrima.notification.discord.repository.DiscordNotificationRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class DiscordNotificationService implements IDiscordNotificationService {

    private final DiscordNotificationRepository discordNotificationRepository;
    private final ObjectMapper objectMapper;

    @Override
    @Transactional
    @WithSpan
    public void publish(
            @SpanAttribute("discord.guild_id") Long guildId,
            @SpanAttribute("discord.channel_id") Long channelId,
            @SpanAttribute("discord.type") String type,
            IDiscordNotificationContent content,
            @SpanAttribute("discord.idempotency_key") String idempotencyKey) {
        log.info(
                "Publishing Discord notification guildId={} channelId={} type={} idempotencyKey={}",
                guildId,
                channelId,
                type,
                idempotencyKey);
        if (guildId == null) {
            log.warn(
                    "Discord publish rejected - guildId cannot be null idempotencyKey={}", idempotencyKey);
            throw new IllegalArgumentException("guildId cannot be null");
        }

        if (channelId == null) {
            log.warn(
                    "Discord publish rejected - channelId cannot be null idempotencyKey={}", idempotencyKey);
            throw new IllegalArgumentException("channelId cannot be null");
        }

        if (type == null || type.isBlank()) {
            log.warn(
                    "Discord publish rejected - type must not be blank idempotencyKey={}", idempotencyKey);
            throw new IllegalArgumentException("type must not be blank");
        }

        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            log.warn("Discord publish rejected - idempotencyKey must not be blank");
            throw new IllegalArgumentException("idempotencyKey must not be blank");
        }

        if (discordNotificationRepository.existsByIdempotencyKey(idempotencyKey)) {
            log.info(
                    "Duplicate Discord notification ignored idempotencyKey={} type={}", idempotencyKey, type);
            return;
        }

        DiscordNotification saved =
                discordNotificationRepository.save(
                        DiscordNotification.builder()
                                .guildId(guildId)
                                .channelId(channelId)
                                .type(type)
                                .content(serialize(content))
                                .idempotencyKey(idempotencyKey)
                                .build());
        log.info(
                "Discord notification enqueued id={} guildId={} channelId={} type={} idempotencyKey={}",
                saved.getId(),
                guildId,
                channelId,
                type,
                idempotencyKey);
    }

    private String serialize(IDiscordNotificationContent content) {
        try {
            return objectMapper.writeValueAsString(content);
        } catch (JsonProcessingException e) {
            throw new IllegalArgumentException("Failed to serialize Discord notification content", e);
        }
    }
}
