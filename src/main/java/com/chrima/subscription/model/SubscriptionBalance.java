package com.chrima.subscription.model;

import com.chrima.subscription.api.enums.SubscriptionStatus;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.Instant;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(
    name = "subscription_balances",
    uniqueConstraints = {
      @UniqueConstraint(
          name = "uq_subscription_balances_group_user_product",
          columnNames = {"external_id", "platform_user_id", "product_id"})
    })
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class SubscriptionBalance {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(name = "external_id", nullable = false)
  private String externalId;

  @Setter
  @Column(name = "platform_user_id", nullable = false)
  private String platformUserId;

  @Setter
  @Column(name = "product_id", nullable = false)
  private UUID productId;

  @Setter
  @Column(name = "credit_amount", nullable = false)
  private double creditAmount;

  @Setter
  @Column(name = "cycle_start")
  private Integer cycleStart;

  @Setter
  @Column(name = "cycle_end")
  private Integer cycleEnd;

  @Setter
  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private SubscriptionStatus status;

  @Setter
  @Column(name = "last_processed_tx")
  private UUID lastProcessedTx;

  @Setter @Builder.Default private int attemptCount = 0;

  @Setter
  @Column(name = "last_notified_at")
  private Integer lastNotifiedAt;

  @CreationTimestamp
  @Column(nullable = false, updatable = false)
  private Instant createdAt;

  @UpdateTimestamp
  @Column(nullable = false)
  private Instant updatedAt;

  protected SubscriptionBalance() {}
}
