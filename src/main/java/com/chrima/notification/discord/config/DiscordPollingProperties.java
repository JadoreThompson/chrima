package com.chrima.notification.discord.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "discord.polling")
public class DiscordPollingProperties {

  private boolean enabled = true;
  private long fixedDelay = 5000;
  private long initialDelay = 1000;
  private int batchSize = 100;
  private int maxAttempts = 3;
}
