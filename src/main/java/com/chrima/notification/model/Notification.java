package com.chrima.notification.model;

import com.chrima.notification.api.enums.ChannelType;
import com.chrima.notification.model.enums.NotificationStatus;
import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "notifications")
@Data
public class Notification {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(nullable = false)
  private String recipient;

  @Column(nullable = false, columnDefinition = "text")
  private String content;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private ChannelType channel;

  @Column(nullable = false, unique = true)
  private String idempotencyKey;

  @Column(nullable = false, updatable = false)
  @CreationTimestamp
  private Instant createdAt;

  @Column(nullable = false)
  private Integer attempts = 0;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private NotificationStatus status = NotificationStatus.PENDING;

  private Instant lastAttemptedAt;

  @Column private Instant dispatchedAt;

  public void markDispatched() {
    this.dispatchedAt = Instant.now();
  }
}
