package com.chrima.wallet.repository;

import com.chrima.wallet.model.Wallet;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface WalletRepository extends JpaRepository<Wallet, UUID> {

  Optional<Wallet> findByIdAndWorkspaceId(UUID id, UUID workspaceId);

  List<Wallet> findByWorkspaceId(UUID workspaceId);

  List<Wallet> findByWorkspaceId(UUID workspaceId, Pageable pageable);

  @Query(
      value =
          "SELECT * FROM wallets WHERE workspace_id = :workspaceId OFFSET :offset LIMIT :limitPlusOne",
      nativeQuery = true)
  List<Wallet> findByWorkspaceIdPaged(
      @Param("workspaceId") UUID workspaceId,
      @Param("offset") int offset,
      @Param("limitPlusOne") int limitPlusOne);
}
