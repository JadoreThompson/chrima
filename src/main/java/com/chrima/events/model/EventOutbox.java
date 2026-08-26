package com.chrima.events.model;

import com.chrima.events.model.enums.EventStatus;
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
@Table(name = "event_outbox")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class EventOutbox {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(nullable = false)
  private String eventType;

  @Column(nullable = false, columnDefinition = "text")
  private String payload;

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
  private EventStatus status = EventStatus.PENDING;

  @Setter private Instant lastAttemptedAt;

  @Setter @Column private Instant dispatchedAt;

  protected EventOutbox() {}

  public void markDispatched() {
    this.dispatchedAt = Instant.now();
  }
}
