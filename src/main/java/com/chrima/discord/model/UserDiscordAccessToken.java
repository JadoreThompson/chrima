package com.chrima.discord.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
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
import org.hibernate.annotations.UpdateTimestamp;

/**
 * Stores OAuth tokens for workspace owners (Chrima users).
 *
 * <p>Keyed by the Chrima user UUID (1:1 with the users table). This is a standalone table holding
 * the full encrypted token — NOT a bridge to {@link DiscordAccessToken}. This separation means a
 * workspace owner can also be a customer without conflicting with {@code discord_access_tokens}'s
 * unique constraint on Discord user ID: the owner's token lives here, the customer's token (if any)
 * lives in {@code discord_access_tokens}.
 */
@Entity
@Table(name = "user_discord_access_tokens")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class UserDiscordAccessToken {

  @Id
  @Column(name = "user_id")
  private UUID userId;

  @Setter
  @Column(name = "discord_user_id", nullable = false)
  private long discordUserId;

  @Setter
  @Column(nullable = false, columnDefinition = "text")
  private String payload;

  @CreationTimestamp
  @Column(nullable = false, updatable = false)
  private Instant createdAt;

  @UpdateTimestamp
  @Column(nullable = false)
  private Instant updatedAt;

  protected UserDiscordAccessToken() {}
}
