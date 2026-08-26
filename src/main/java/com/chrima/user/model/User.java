package com.chrima.user.model;

import com.chrima.user.model.enums.Tier;
import jakarta.persistence.*;
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

  @Setter
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
}
