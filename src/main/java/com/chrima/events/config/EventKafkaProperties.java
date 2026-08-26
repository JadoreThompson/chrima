package com.chrima.events.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "events.kafka")
public class EventKafkaProperties {

  /** Default topic for all domain events. Consumers filter by header `eventType`. */
  private String topic = "chrima.events";
}
