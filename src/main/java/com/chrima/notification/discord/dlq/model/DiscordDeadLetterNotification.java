package com.chrima.notification.discord.dlq.model;

import com.chrima.notification.discord.dlq.model.enums.DiscordDeadLetterStatus;
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
@Table(name = "discord_dead_letter_notifications")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class DiscordDeadLetterNotification {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column private UUID discordNotificationId;

  @Column(nullable = false)
  private Long guildId;

  @Column(nullable = false)
  private Long channelId;

  @Column(nullable = false)
  private String type;

  @Column(nullable = false, columnDefinition = "text")
  private String content;

  @Column(nullable = false)
  private String idempotencyKey;

  @Column(columnDefinition = "text")
  private String failureReason;

  @Setter @Builder.Default private Integer attempts = 0;

  @Setter
  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  @Builder.Default
  private DiscordDeadLetterStatus status = DiscordDeadLetterStatus.PENDING;

  @Column(nullable = false, updatable = false)
  @CreationTimestamp
  private Instant createdAt;

  @Setter private Instant lastAttemptedAt;

  @Setter private Instant nextAttemptAt;

  @Setter private Instant dispatchedAt;

  protected DiscordDeadLetterNotification() {}

  public void markDispatched() {
    this.dispatchedAt = Instant.now();
  }
}
