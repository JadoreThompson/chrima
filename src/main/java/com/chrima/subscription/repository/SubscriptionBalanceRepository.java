package com.chrima.subscription.repository;

import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.model.SubscriptionBalance;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface SubscriptionBalanceRepository extends JpaRepository<SubscriptionBalance, UUID> {

  Optional<SubscriptionBalance> findByExternalIdAndPlatformUserIdAndProductId(
      String externalId, String platformUserId, UUID productId);

  List<SubscriptionBalance> findByPlatformUserIdAndExternalId(
      String platformUserId, String externalId);

  @Query(
      """
          select b from SubscriptionBalance b
          where b.cycleEnd is not null
            and b.attemptCount < :maxAttempts
            and ((b.cycleEnd <= :windowEnd and b.cycleEnd >= :now and b.status = :active)
                 or (b.cycleEnd < :now and b.status <> :cancelled))
            and (b.lastNotifiedAt is null or b.lastNotifiedAt <= :cooldownBefore)
          """)
  List<SubscriptionBalance> findDueForExpiryCheck(
      @Param("maxAttempts") int maxAttempts,
      @Param("windowEnd") long windowEnd,
      @Param("now") long now,
      @Param("cooldownBefore") long cooldownBefore,
      @Param("active") SubscriptionStatus active,
      @Param("cancelled") SubscriptionStatus cancelled);
}
