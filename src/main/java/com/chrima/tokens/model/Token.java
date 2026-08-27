package com.chrima.tokens.model;

import com.chrima.tokens.model.enums.TokenChain;
import com.chrima.tokens.model.enums.TokenStandard;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Entity
@Table(name = "tokens")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
public class Token {

  @Id
  @GeneratedValue(strategy = GenerationType.UUID)
  private UUID id;

  @Column(nullable = false)
  private String name;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private TokenStandard standard;

  @Enumerated(EnumType.STRING)
  @Column(nullable = false)
  private TokenChain chain;

  @Column(nullable = false)
  private String address;

  protected Token() {}
}
