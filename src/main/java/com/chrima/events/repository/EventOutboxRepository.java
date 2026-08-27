package com.chrima.events.repository;

import static jakarta.persistence.LockModeType.PESSIMISTIC_WRITE;

import com.chrima.events.model.EventOutbox;
import jakarta.persistence.QueryHint;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.QueryHints;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public interface EventOutboxRepository extends JpaRepository<EventOutbox, UUID> {

  boolean existsByIdempotencyKey(String idempotencyKey);

  @Transactional
  @Lock(PESSIMISTIC_WRITE)
  @Query(
      "select e from EventOutbox e where e.dispatchedAt is null and e.status = 'PENDING' order by e.createdAt")
  @QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
  List<EventOutbox> findPending(Pageable pageable);
}
