package com.chrima.notification.discord.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(DiscordPollingProperties.class)
public class DiscordPollingConfig {}
