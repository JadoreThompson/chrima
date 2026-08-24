package com.chrima.notification.channel;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.api.model.INotificationContent;

public interface INotificationChannel<T extends INotificationContent> {

  boolean supports(ChannelType channelType);

  void dispatch(String recipient, T content);
}
