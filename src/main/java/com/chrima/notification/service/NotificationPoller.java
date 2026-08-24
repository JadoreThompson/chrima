package com.chrima.notification.service;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.EmailNotificationContent;
import com.chrima.notification.channel.INotificationChannel;
import com.chrima.notification.dlq.service.DeadLetterService;
import com.chrima.notification.model.Notification;
import com.chrima.notification.model.enums.NotificationStatus;
import com.chrima.notification.repository.NotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.NoSuchElementException;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.Pageable;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Component
@RequiredArgsConstructor
public class NotificationPoller {

  private final NotificationRepository notificationRepository;

  private final List<INotificationChannel<?>> notificationChannels;

  private final ObjectMapper objectMapper;

  private final DeadLetterService deadLetterService;

  @Value("${notification.polling.batch-size:100}")
  private int batchSize;

  @Value("${notification.polling.max-attempts:3}")
  private int maxAttempts;

  @Scheduled(fixedDelayString = "${notification.polling.delay}")
  @Transactional
  public void run() {
    List<Notification> notifications =
        notificationRepository.findPending(Pageable.ofSize(batchSize));

    for (Notification notification : notifications) {
      try {
        INotificationChannel<?> channel =
            notificationChannels.stream()
                .filter(ch -> ch.supports(notification.getChannel()))
                .findFirst()
                .orElseThrow();
        if (notification.getChannel() == ChannelType.EMAIL) {
          EmailNotificationContent content =
              objectMapper.readValue(notification.getContent(), EmailNotificationContent.class);
          @SuppressWarnings("unchecked")
          INotificationChannel<EmailNotificationContent> emailChannel =
              (INotificationChannel<EmailNotificationContent>) channel;
          emailChannel.dispatch(notification.getRecipient(), content);
        } else {
          log.error(
              "Content class for notification channel '{}' not found", notification.getChannel());
          throw new IllegalStateException(
              "Content class for notification channel '"
                  + notification.getChannel()
                  + "' not found");
        }

        int updatedAttempts =
            (notification.getAttempts() == null ? 0 : notification.getAttempts()) + 1;
        notification.setAttempts(updatedAttempts);
        notification.setLastAttemptedAt(Instant.now());
        notification.markDispatched();
        notification.setStatus(NotificationStatus.COMPLETED);
      } catch (Exception e) {
        log.info("Before attempts={}", notification.getAttempts());
        int updatedAttempts =
            (notification.getAttempts() == null ? 0 : notification.getAttempts()) + 1;
        notification.setAttempts(updatedAttempts);
        notification.setLastAttemptedAt(Instant.now());
        if (updatedAttempts >= maxAttempts) {
          notification.setStatus(NotificationStatus.FAILED);
          try {
            deadLetterService.enqueue(notification, e.getMessage());
          } catch (Exception dlqEx) {
            log.error("Failed to enqueue notification {} to DLQ", notification.getId(), dlqEx);
          }
        }
        if (e instanceof NoSuchElementException) {
          log.warn(
              "No implementation found for notification channel '{}'",
              notification.getChannel(),
              e);
        } else if (e instanceof IOException) {
          log.error(e.getMessage(), e);
        } else {
          log.error("Failed to dispatch notification {}", notification.getId(), e);
        }
      }

      log.info("After attempts={}", notification.getAttempts());
    }

    //        notificationRepository.saveAll(notifications);
  }
}
