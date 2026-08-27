package com.chrima.subscription.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "subscription.expiry")
public class SubscriptionExpiryProperties {

  private boolean enabled = true;

  private long fixedDelay = 3600000;

  private long initialDelay = 60000;

  private int notificationCooldown = 6 * 3600;

  private int expiryWindow = 12 * 3600;

  private int maxAttempts = 2;
}
