package com.chrima.product.model;

import com.chrima.product.api.enums.FulfilmentType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

@Entity
@Table(name = "products")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class Product {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(name = "workspace_id", nullable = false)
  private UUID workspaceId;

  @Setter
  @Column(nullable = false)
  private String name;

  @Setter
  @Column(length = 256)
  private String description;

  @Setter
  @Column(name = "wallet_id", nullable = false)
  private UUID walletId;

  @Enumerated(EnumType.STRING)
  @Column(name = "fulfilment_type", nullable = false)
  private FulfilmentType fulfilmentType;

  @Setter
  @Column(name = "external_url")
  private String externalUrl;

  @Setter
  @JdbcTypeCode(SqlTypes.JSON)
  @Column(columnDefinition = "jsonb")
  private List<String> roles;

  @CreationTimestamp
  @Column(nullable = false, updatable = false)
  private Instant createdAt;

  @UpdateTimestamp
  @Column(nullable = false)
  private Instant updatedAt;

  protected Product() {}
}
