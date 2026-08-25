package com.chrima.notification.dlq.service;

import com.chrima.notification.dlq.config.DeadLetterProperties;
import com.chrima.notification.dlq.model.DeadLetterNotification;
import com.chrima.notification.dlq.model.enums.DeadLetterStatus;
import com.chrima.notification.dlq.repository.DeadLetterNotificationRepository;
import com.chrima.notification.model.Notification;
import java.time.Instant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class DeadLetterService {

  private final DeadLetterNotificationRepository deadLetterNotificationRepository;
  private final DeadLetterProperties properties;

  @Transactional
  public DeadLetterNotification enqueue(Notification notification, String failureReason) {
    log.info(
        "Enqueueing notification to DLQ id={} idempotencyKey={} channel={} failureReason='{}'",
        notification.getId(),
        notification.getIdempotencyKey(),
        notification.getChannel(),
        failureReason);
    Instant nextAttemptAt = Instant.now().plus(properties.getInitialDelay());
    DeadLetterNotification deadLetter =
        DeadLetterNotification.builder()
            .notificationId(notification.getId())
            .recipient(notification.getRecipient())
            .content(notification.getContent())
            .channel(notification.getChannel())
            .idempotencyKey(notification.getIdempotencyKey())
            .failureReason(failureReason)
            .attempts(0)
            .status(DeadLetterStatus.PENDING)
            .nextAttemptAt(nextAttemptAt)
            .build();
    DeadLetterNotification saved = deadLetterNotificationRepository.save(deadLetter);
    log.info(
        "DLQ entry created id={} notificationId={} nextAttemptAt={}",
        saved.getId(),
        notification.getId(),
        nextAttemptAt);
    return saved;
  }
}
