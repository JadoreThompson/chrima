package com.chrima.user.model;

import com.chrima.user.model.enums.Tier;
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
    name = "users",
    uniqueConstraints = {
      @UniqueConstraint(name = "uq_users_username", columnNames = "username"),
      @UniqueConstraint(name = "uq_users_email", columnNames = "email")
    })
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class User {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(nullable = false)
  private String username;

  @Setter
  @Column(nullable = false)
  private String email;

  @Setter
  @Column(nullable = false)
  private String password;

  @Setter @Column private String jwtToken;

  @Setter
  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  @Builder.Default
  private Tier tier = Tier.FREE;

  @CreationTimestamp
  @Column(nullable = false, updatable = false)
  private Instant createdAt;

  @UpdateTimestamp
  @Column(nullable = false)
  private Instant updatedAt;

  protected User() {}

  public void setUsername(String username) {
    this.username = username;
  }

  @jakarta.persistence.PrePersist
  void prePersist() {
    Instant now = Instant.now();
    if (createdAt == null) {
      createdAt = now;
    }
    if (updatedAt == null) {
      updatedAt = now;
    }
  }

  @jakarta.persistence.PreUpdate
  void preUpdate() {
    updatedAt = Instant.now();
  }
}
