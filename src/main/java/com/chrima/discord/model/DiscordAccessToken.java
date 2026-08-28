package com.chrima.discord.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

/**
 * Stores OAuth tokens for product subscribers/purchasers (customers).
 *
 * <p>Keyed by Discord user ID (snowflake). A customer is identified solely by their Discord
 * snowflake — they have no Chrima user account UUID. There is at most one row per Discord user so
 * the same person buying multiple products shares the same token row.
 */
@Entity
@Table(name = "discord_access_tokens")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class DiscordAccessToken {

  @Id
  @Column(name = "user_id")
  private long userId;

  @Setter
  @Column(nullable = false, columnDefinition = "text")
  private String payload;

  @CreationTimestamp
  @Column(nullable = false, updatable = false)
  private Instant createdAt;

  @UpdateTimestamp
  @Column(nullable = false)
  private Instant updatedAt;

  protected DiscordAccessToken() {}
}
