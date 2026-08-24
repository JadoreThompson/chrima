package com.chrima.notification.service;

import com.chrima.notification.api.INotificationService;
import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.INotificationContent;
import com.chrima.notification.model.Notification;
import com.chrima.notification.repository.NotificationRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.mail.internet.AddressException;
import jakarta.mail.internet.InternetAddress;
import java.io.IOException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class NotificationService implements INotificationService {

  private final NotificationRepository notificationRepository;
  private final ObjectMapper objectMapper;

  @Override
  @Transactional
  public void publish(
      String recipient, ChannelType channel, INotificationContent content, String idempotencyKey)
      throws IOException {
    if (idempotencyKey == null || idempotencyKey.isBlank()) {
      throw new IllegalArgumentException("idempotencyKey must not be blank");
    }

    if (channel == ChannelType.EMAIL) {
      validateEmail(recipient);
    }

    if (notificationRepository.existsByIdempotencyKey(idempotencyKey)) {
      return;
    }

    Notification notification = new Notification();
    notification.setRecipient(recipient);
    notification.setChannel(channel);
    notification.setContent(objectMapper.writeValueAsString(content));
    notification.setIdempotencyKey(idempotencyKey);

    notificationRepository.save(notification);
  }

  private void validateEmail(String recipient) {
    if (recipient == null || recipient.isBlank()) {
      throw new IllegalArgumentException("recipient must not be blank");
    }
    try {
      InternetAddress address = new InternetAddress(recipient, true);
      address.validate();
    } catch (AddressException e) {
      throw new IllegalArgumentException("Invalid email address: " + recipient, e);
    }
  }
}
