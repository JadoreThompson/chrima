package com.chrima.notification.discord.dlq.service;

import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.channel.DiscordNotificationChannel;
import com.chrima.notification.discord.dlq.config.DiscordDeadLetterProperties;
import com.chrima.notification.discord.dlq.model.DiscordDeadLetterNotification;
import com.chrima.notification.discord.dlq.model.enums.DiscordDeadLetterStatus;
import com.chrima.notification.discord.dlq.repository.DiscordDeadLetterNotificationRepository;
import com.chrima.notification.discord.model.DiscordNotificationContentRegistry;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.instrumentation.annotations.WithSpan;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.NoSuchElementException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
public class DiscordDeadLetterPoller {

    private final DiscordDeadLetterNotificationRepository discordDeadLetterNotificationRepository;
    private final DiscordDeadLetterProperties properties;
    private final DiscordNotificationChannel discordNotificationChannel;
    private final ObjectMapper objectMapper;
    private final DiscordNotificationContentRegistry registry;

    @Scheduled(fixedDelayString = "${discord.dlq.polling-delay:5000}")
    @Transactional
    @WithSpan
    public void run() {
        List<DiscordDeadLetterNotification> entries =
                discordDeadLetterNotificationRepository.findReady(
                        Instant.now(), Pageable.ofSize(properties.getBatchSize()));

        if (entries.isEmpty()) {
            log.debug("Discord DLQ poller - no ready entries batchSize={}", properties.getBatchSize());
            return;
        }

        log.info(
                "Discord DLQ poller - processing batch size={} maxAttempts={}",
                entries.size(),
                properties.getMaxAttempts());

        for (DiscordDeadLetterNotification entry : entries) {
            log.debug(
                    "Retrying Discord DLQ entry id={} discordNotificationId={} type={} attempt={}/{}",
                    entry.getId(),
                    entry.getDiscordNotificationId(),
                    entry.getType(),
                    entry.getAttempts() == null ? 1 : entry.getAttempts() + 1,
                    properties.getMaxAttempts());
            try {
                IDiscordNotificationContent content =
                        objectMapper.readValue(entry.getContent(), registry.get(entry.getType()));
                Long discordMessageId =
                        discordNotificationChannel.send(
                                entry.getGuildId(), entry.getChannelId(), content, entry.getIdempotencyKey());

                int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
                entry.setAttempts(updatedAttempts);
                entry.setLastAttemptedAt(Instant.now());
                entry.markDispatched();
                entry.setStatus(DiscordDeadLetterStatus.COMPLETED);
                log.info(
                        "Discord DLQ entry dispatched id={} discordNotificationId={} type={} discordMessageId={} attempts={}",
                        entry.getId(),
                        entry.getDiscordNotificationId(),
                        entry.getType(),
                        discordMessageId,
                        updatedAttempts);
            } catch (Exception e) {
                int updatedAttempts = (entry.getAttempts() == null ? 0 : entry.getAttempts()) + 1;
                entry.setAttempts(updatedAttempts);
                entry.setLastAttemptedAt(Instant.now());
                if (updatedAttempts >= properties.getMaxAttempts()) {
                    entry.setStatus(DiscordDeadLetterStatus.FAILED);
                    log.warn(
                            "Discord DLQ entry id={} permanently failed after {}/{} attempts type={}",
                            entry.getId(),
                            updatedAttempts,
                            properties.getMaxAttempts(),
                            entry.getType());
                } else {
                    Instant nextAttempt = calculateNextAttempt(updatedAttempts);
                    entry.setNextAttemptAt(nextAttempt);
                    log.warn(
                            "Discord DLQ retry failed id={} type={} attempt={}/{} nextAttemptAt={}",
                            entry.getId(),
                            entry.getType(),
                            updatedAttempts,
                            properties.getMaxAttempts(),
                            nextAttempt,
                            e);
                }
                if (e instanceof NoSuchElementException) {
                    log.warn("No implementation found for Discord DLQ type '{}'", entry.getType(), e);
                } else {
                    log.error("Failed to dispatch Discord DLQ notification {}", entry.getId(), e);
                }
            }
        }

        log.info("Discord DLQ poller - batch completed processed={}", entries.size());
    }

    public Instant calculateNextAttempt(int attempts) {
        return calculateNextAttempt(attempts, Instant.now());
    }

    public Instant calculateNextAttempt(int attempts, Instant now) {
        Duration initialDelay = properties.getInitialDelay();
        double multiplier = properties.getBackoffMultiplier();
        long delayMillis = (long) (initialDelay.toMillis() * Math.pow(multiplier, attempts - 1));
        if (attempts <= 1) {
            delayMillis = initialDelay.toMillis();
        }
        return now.plusMillis(delayMillis);
    }
}
