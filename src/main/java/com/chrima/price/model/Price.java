package com.chrima.price.model;

import com.chrima.price.api.enums.Currency;
import com.chrima.price.api.enums.PriceType;
import com.chrima.price.api.enums.RecurringInterval;
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
import org.hibernate.annotations.UpdateTimestamp;

@Entity
@Table(name = "prices")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class Price {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(name = "workspace_id", nullable = false)
  private UUID workspaceId;

  @Column(name = "product_id", nullable = false)
  private UUID productId;

  @Setter
  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private PriceType type;

  @Setter
  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private Currency currency;

  @Setter
  @Column(nullable = false)
  private double amount;

  @Setter
  @Enumerated(EnumType.STRING)
  @Column(name = "recurring_interval")
  private RecurringInterval recurringInterval;

  @Setter
  @Column(name = "recurring_interval_count")
  private Integer recurringIntervalCount;

  @Setter
  @Column(name = "trial_period_days")
  private Integer trialPeriodDays;

  @CreationTimestamp
  @Column(nullable = false, updatable = false)
  private Instant createdAt;

  @UpdateTimestamp
  @Column(nullable = false)
  private Instant updatedAt;

  protected Price() {}
}
