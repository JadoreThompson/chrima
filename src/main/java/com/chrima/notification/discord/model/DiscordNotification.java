package com.chrima.notification.discord.model;

import com.chrima.notification.discord.model.enums.DiscordNotificationStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "discord_notifications")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class DiscordNotification {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(nullable = false)
  private Long guildId;

  @Column(nullable = false)
  private Long channelId;

  @Column(nullable = false)
  private String type;

  @Column(nullable = false, columnDefinition = "text")
  private String content;

  @Column private Long discordMessageId;

  @Column(nullable = false, unique = true)
  private String idempotencyKey;

  @Column(nullable = false, updatable = false)
  @CreationTimestamp
  private Instant createdAt;

  @Setter @Builder.Default private Integer attempts = 0;

  @Setter
  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  @Builder.Default
  private DiscordNotificationStatus status = DiscordNotificationStatus.PENDING;

  @Setter private Instant lastAttemptedAt;

  @Setter @Column private Instant dispatchedAt;

  protected DiscordNotification() {}

  public void markDispatched(Long discordMessageId) {
    this.discordMessageId = discordMessageId;
    this.dispatchedAt = Instant.now();
  }

  public void markDispatched() {
    this.dispatchedAt = Instant.now();
  }
}
