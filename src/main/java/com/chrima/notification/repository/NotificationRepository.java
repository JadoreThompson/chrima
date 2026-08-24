package com.chrima.notification.repository;

import static jakarta.persistence.LockModeType.PESSIMISTIC_WRITE;

import com.chrima.notification.model.Notification;
import jakarta.persistence.QueryHint;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.QueryHints;
import org.springframework.transaction.annotation.Transactional;

public interface NotificationRepository extends JpaRepository<Notification, UUID> {

  boolean existsByIdempotencyKey(String idempotencyKey);

  @Transactional
  @Lock(PESSIMISTIC_WRITE)
  @Query(
      "select n from Notification n where n.dispatchedAt is null and n.status = 'PENDING' order by n.createdAt")
  @QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
  List<Notification> findPending(Pageable pageable);
}
