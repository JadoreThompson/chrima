package com.chrima.wallet.repository;

import com.chrima.wallet.model.Wallet;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface WalletRepository extends JpaRepository<Wallet, UUID> {

  Optional<Wallet> findByIdAndWorkspaceId(UUID id, UUID workspaceId);

  List<Wallet> findByWorkspaceId(UUID workspaceId);

  Page<Wallet> findByWorkspaceId(UUID workspaceId, Pageable pageable);
}
