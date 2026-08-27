package com.chrima.events.dlq.repository;

import static jakarta.persistence.LockModeType.PESSIMISTIC_WRITE;

import com.chrima.events.dlq.model.EventDeadLetter;
import jakarta.persistence.QueryHint;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.QueryHints;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

@Repository
public interface EventDeadLetterRepository extends JpaRepository<EventDeadLetter, UUID> {

  @Transactional
  @Lock(PESSIMISTIC_WRITE)
  @Query(
      "select d from EventDeadLetter d where d.status = 'PENDING' and d.nextAttemptAt <= :now order by d.nextAttemptAt")
  @QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
  List<EventDeadLetter> findReady(@Param("now") Instant now, Pageable pageable);
}
