package com.chrima.price.repository;

import com.chrima.price.model.Price;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface PriceRepository extends JpaRepository<Price, UUID> {

  Optional<Price> findByIdAndWorkspaceId(UUID id, UUID workspaceId);

  Page<Price> findByProductId(UUID productId, Pageable pageable);
}
