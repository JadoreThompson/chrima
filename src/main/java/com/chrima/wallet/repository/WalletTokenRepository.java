package com.chrima.wallet.repository;

import com.chrima.wallet.model.WalletToken;
import com.chrima.wallet.model.WalletTokenId;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface WalletTokenRepository extends JpaRepository<WalletToken, WalletTokenId> {

  List<WalletToken> findByWalletId(UUID walletId);

  @Query("SELECT wt.tokenId FROM WalletToken wt WHERE wt.walletId = :walletId")
  List<UUID> findTokenIdsByWalletId(@Param("walletId") UUID walletId);
}
