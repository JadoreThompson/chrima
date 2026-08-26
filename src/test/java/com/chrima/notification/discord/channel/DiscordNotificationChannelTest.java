package com.chrima.notification.discord.channel;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.notification.discord.api.IDiscordNotificationBuilder;
import com.chrima.notification.discord.api.IDiscordNotificationContent;
import com.chrima.notification.discord.config.DiscordConfig;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.UUID;
import net.dv8tion.jda.api.JDA;
import net.dv8tion.jda.api.entities.Message;
import net.dv8tion.jda.api.entities.MessageEmbed;
import net.dv8tion.jda.api.entities.channel.concrete.TextChannel;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;

@SpringBootTest(
    classes = {
      DiscordNotificationChannel.class,
      DiscordConfig.class,
      DiscordNotificationChannelTest.TestBuilderConfig.class
    })
class DiscordNotificationChannelTest {

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("discord.token", () -> resolveProperty("DISCORD_TOKEN", "discord.token"));
    registry.add(
        "discord.test.guild-id",
        () -> resolveProperty("DISCORD_TEST_GUILD_ID", "discord.test.guild-id"));
    registry.add(
        "discord.test.channel-id",
        () -> resolveProperty("DISCORD_TEST_CHANNEL_ID", "discord.test.channel-id"));
  }

  private static String resolveProperty(String envKey, String propertyKey) {
    String envValue = System.getenv(envKey);
    if (envValue != null && !envValue.isBlank()) {
      return envValue;
    }
    try {
      Path dotEnv = Path.of(".env");
      if (Files.exists(dotEnv)) {
        for (String line : Files.readAllLines(dotEnv)) {
          line = line.trim();
          if (line.startsWith(envKey + "=")) {
            String v = line.substring(envKey.length() + 1).trim();
            if ((v.startsWith("\"") && v.endsWith("\""))
                || (v.startsWith("'") && v.endsWith("'"))) {
              v = v.substring(1, v.length() - 1);
            }
            return v;
          }
        }
      }
      Path altEnv = Path.of("src/main/resources/application.yaml");
      if (Files.exists(altEnv)) {
        // fallback: try to read from already resolved spring property via placeholder?
      }
    } catch (IOException ignored) {
    }
    return "";
  }

  @TestConfiguration
  static class TestBuilderConfig {
    @Bean
    IDiscordNotificationBuilder<TestContent> testDiscordBuilder() {
      return new IDiscordNotificationBuilder<TestContent>() {
        @Override
        public boolean supports(Class<? extends IDiscordNotificationContent> contentType) {
          return TestContent.class.equals(contentType);
        }

        @Override
        public MessageEmbed build(TestContent content) {
          return new net.dv8tion.jda.api.EmbedBuilder()
              .setTitle("Chrima Integration Test")
              .setDescription("Test at " + Instant.now() + " body=" + content.body())
              .setFooter("idempotency=" + UUID.randomUUID())
              .build();
        }
      };
    }
  }

  @Autowired private DiscordNotificationChannel channel;

  @Autowired private JDA jda;

  @Value("${discord.token}")
  private String discordToken;

  @Value("${discord.test.guild-id}")
  private Long testGuildId;

  @Value("${discord.test.channel-id}")
  private Long testChannelId;

  @Test
  void sendShouldDeliverRealMessageAndVerifyByFetching() throws Exception {
    assertThat(discordToken).as("discord.token property").isNotBlank();
    assertThat(testGuildId).as("discord.test.guild-id property").isNotNull().isGreaterThan(0);
    assertThat(testChannelId).as("discord.test.channel-id property").isNotNull().isGreaterThan(0);
    assertThat(jda).isNotNull();

    jda.awaitReady();

    String idempotencyKey = UUID.randomUUID().toString();
    TestContent content = new TestContent();

    Long messageId = channel.send(testGuildId, testChannelId, content, idempotencyKey);

    assertThat(messageId).isNotNull().isGreaterThan(0);

    TextChannel tc = jda.getGuildById(testGuildId).getTextChannelById(testChannelId);
    assertThat(tc).as("TextChannel from injected properties").isNotNull();

    Message retrieved = tc.retrieveMessageById(messageId).complete();
    assertThat(retrieved).isNotNull();
    assertThat(retrieved.getIdLong()).isEqualTo(messageId);
    assertThat(retrieved.getEmbeds()).isNotEmpty();

    //    retrieved.delete().complete();
  }

  static class TestContent implements IDiscordNotificationContent {

    @Override
    public String subject() {
      return "Integration Subject";
    }

    @Override
    public String body() {
      return "Integration Body " + Instant.now();
    }
  }
}
