package com.chrima.notification.api;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.INotificationContent;
import java.io.IOException;

public interface INotificationService {

  void publish(
      String recipient, ChannelType channel, INotificationContent content, String idempotencyKey)
      throws IOException;
}
