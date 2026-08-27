package com.chrima.transaction.repository;

import com.chrima.transaction.model.Transaction;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, UUID> {

  Page<Transaction> findBySenderOrderByTimestampDesc(String sender, Pageable pageable);

  Page<Transaction> findByProductIdOrderByTimestampDesc(UUID productId, Pageable pageable);

  Page<Transaction> findByPriceIdOrderByTimestampDesc(UUID priceId, Pageable pageable);

  @Query(
      value =
          """
          select t from Transaction t
          join Price p on p.id = t.priceId
          where (:workspaceId is null or p.workspaceId = :workspaceId)
            and (:productId is null or t.productId = :productId)
            and (:priceId is null or t.priceId = :priceId)
            and (:sender is null or t.sender = :sender)
          order by t.timestamp desc
          """,
      countQuery =
          """
          select count(t) from Transaction t
          join Price p on p.id = t.priceId
          where (:workspaceId is null or p.workspaceId = :workspaceId)
            and (:productId is null or t.productId = :productId)
            and (:priceId is null or t.priceId = :priceId)
            and (:sender is null or t.sender = :sender)
          """)
  Page<Transaction> findFiltered(
      @Param("workspaceId") UUID workspaceId,
      @Param("productId") UUID productId,
      @Param("priceId") UUID priceId,
      @Param("sender") String sender,
      Pageable pageable);
}
