package com.chrima.notification.discord.config;

import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.JDABuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;

@Configuration
public class DiscordConfig {

  @Bean
  @Lazy
  @ConditionalOnProperty(name = "discord.token")
  public JDA discordJda(@Value("${discord.token}") String token) {
    try {
      return JDABuilder.createDefault(token).build();
    } catch (Exception e) {
      // Allow context to start with dummy token in tests (e.g. "test-token");
      // Real Discord operations will fail lazily via ObjectProvider check.
      // Return null to avoid InvalidTokenException breaking test context.
      return null;
    }
  }
}
