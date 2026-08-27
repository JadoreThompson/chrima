package com.chrima.wallet.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.IdClass;
import jakarta.persistence.Table;
import java.util.UUID;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Entity
@Table(name = "wallet_tokens")
@Getter
@Builder
@AllArgsConstructor(access = AccessLevel.PACKAGE)
@IdClass(WalletTokenId.class)
public class WalletToken {

  @Id
  @Column(name = "wallet_id", nullable = false)
  private UUID walletId;

  @Id
  @Column(name = "token_id", nullable = false)
  private UUID tokenId;

  protected WalletToken() {}
}
