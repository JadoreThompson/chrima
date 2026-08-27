package com.chrima.subscription.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(SubscriptionExpiryProperties.class)
public class SubscriptionExpiryConfig {}
