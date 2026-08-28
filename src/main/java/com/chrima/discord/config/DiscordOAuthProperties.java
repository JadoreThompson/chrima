package com.chrima.discord.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Getter
@Setter
@Configuration
@ConfigurationProperties(prefix = "discord.oauth")
public class DiscordOAuthProperties {

  private String clientId = "";

  private String clientSecret = "";

  private String redirectUri = "";

  private String subscriberRedirectUri = "";

  private String apiBaseUrl = "https://discord.com/api";
}
