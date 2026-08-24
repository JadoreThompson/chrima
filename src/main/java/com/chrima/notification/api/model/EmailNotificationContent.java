package com.chrima.notification.api.model;

public record EmailNotificationContent(String subject, String body)
    implements INotificationContent {}
