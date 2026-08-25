package com.chrima.notification.service;

import com.chrima.notification.api.INotificationService;
import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.INotificationContent;
import com.chrima.notification.model.Notification;
import com.chrima.notification.repository.NotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.opentelemetry.instrumentation.annotations.SpanAttribute;
import io.opentelemetry.instrumentation.annotations.WithSpan;
import jakarta.mail.internet.AddressException;
import jakarta.mail.internet.InternetAddress;

import java.io.IOException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificationService implements INotificationService {

    private final NotificationRepository notificationRepository;
    private final ObjectMapper objectMapper;

    @Override
    @Transactional
    @WithSpan
    public void publish(
            @SpanAttribute("notification.recipient") String recipient,
            @SpanAttribute("notification.channel") ChannelType channel,
            INotificationContent content,
            @SpanAttribute("notification.idempotency_key") String idempotencyKey)
            throws IOException {
        log.info(
                "Publishing notification recipient={} channel={} idempotencyKey={}",
                recipient,
                channel,
                idempotencyKey);
        if (idempotencyKey == null || idempotencyKey.isBlank()) {
            log.warn("Publish rejected - idempotencyKey must not be blank recipient={}", recipient);
            throw new IllegalArgumentException("idempotencyKey must not be blank");
        }

        if (channel == ChannelType.EMAIL) {
            validateEmail(recipient);
        }

        if (notificationRepository.existsByIdempotencyKey(idempotencyKey)) {
            log.info(
                    "Duplicate notification ignored idempotencyKey={} channel={} recipient={}",
                    idempotencyKey,
                    channel,
                    recipient);
            return;
        }

        Notification notification = new Notification();
        notification.setRecipient(recipient);
        notification.setChannel(channel);
        notification.setContent(objectMapper.writeValueAsString(content));
        notification.setIdempotencyKey(idempotencyKey);

        Notification saved = notificationRepository.save(notification);
        log.info(
                "Notification enqueued id={} idempotencyKey={} channel={} recipient={}",
                saved.getId(),
                idempotencyKey,
                channel,
                recipient);
    }

    private void validateEmail(String recipient) {
        if (recipient == null || recipient.isBlank()) {
            log.warn("Email validation failed - recipient must not be blank");
            throw new IllegalArgumentException("recipient must not be blank");
        }
        try {
            InternetAddress address = new InternetAddress(recipient, true);
            address.validate();
        } catch (AddressException e) {
            log.warn("Invalid email address recipient={}", recipient, e);
            throw new IllegalArgumentException("Invalid email address: " + recipient, e);
        }
    }
}
