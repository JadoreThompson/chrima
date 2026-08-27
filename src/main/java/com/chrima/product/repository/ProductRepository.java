package com.chrima.product.repository;

import com.chrima.product.model.Product;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ProductRepository extends JpaRepository<Product, UUID> {

  Optional<Product> findByIdAndWorkspaceId(UUID id, UUID workspaceId);

  Page<Product> findByWorkspaceId(UUID workspaceId, Pageable pageable);

  boolean existsByWalletId(UUID walletId);
}
