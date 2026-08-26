package com.chrima.events.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "events.polling")
public class EventPollingProperties {

  private long delay = 5000;

  private int batchSize = 100;

  private int maxAttempts = 3;
}
