package com.chrima.transaction.model;

import com.chrima.transaction.api.enums.TransactionStatus;
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
import org.hibernate.annotations.CreationTimestamp;

@Entity
@Table(name = "transactions")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class Transaction {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(name = "product_id", nullable = false)
  private UUID productId;

  @Column(name = "price_id", nullable = false)
  private UUID priceId;

  @Column(name = "platform_user_id", nullable = false)
  private String platformUserId;

  @Column(nullable = false)
  private String sender;

  @Column(nullable = false)
  private String recipient;

  @Column(nullable = false)
  private String address;

  @Column(nullable = false)
  private double amount;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private TransactionStatus status;

  @Column(nullable = false)
  private int timestamp;

  @CreationTimestamp
  @Column(nullable = false, updatable = false)
  private Instant createdAt;

  protected Transaction() {}
}
