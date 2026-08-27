package com.chrima.notification.discord.repository;

import static jakarta.persistence.LockModeType.PESSIMISTIC_WRITE;

import com.chrima.notification.discord.model.DiscordNotification;
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
public interface DiscordNotificationRepository extends JpaRepository<DiscordNotification, UUID> {

  boolean existsByIdempotencyKey(String idempotencyKey);

  @Transactional
  @Lock(PESSIMISTIC_WRITE)
  @Query(
      "select n from DiscordNotification n where n.dispatchedAt is null and n.status = 'PENDING' order by n.createdAt")
  @QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
  List<DiscordNotification> findPending(Pageable pageable);
}
