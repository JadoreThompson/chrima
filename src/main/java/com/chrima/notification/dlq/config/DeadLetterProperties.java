package com.chrima.notification.dlq.config;

import java.time.Duration;
import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "notification.dlq")
public class DeadLetterProperties {

  private Duration initialDelay = Duration.ofSeconds(5);

  private Duration pollingDelay = Duration.ofSeconds(5);

  private int maxAttempts = 5;

  private double backoffMultiplier = 2.0;

  private int batchSize = 100;
}
