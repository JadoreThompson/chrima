package com.chrima.subscription.api.dto;

import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.model.SubscriptionBalance;
import java.time.Instant;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class SubscriptionBalanceResponse {
  UUID id;
  String externalId;
  String platformUserId;
  UUID productId;
  double creditAmount;
  Integer cycleStart;
  Integer cycleEnd;
  SubscriptionStatus status;
  UUID lastProcessedTx;
  int attemptCount;
  Integer lastNotifiedAt;
  Instant updatedAt;

  public static SubscriptionBalanceResponse from(SubscriptionBalance balance) {
    return SubscriptionBalanceResponse.builder()
        .id(balance.getId())
        .externalId(balance.getExternalId())
        .platformUserId(balance.getPlatformUserId())
        .productId(balance.getProductId())
        .creditAmount(balance.getCreditAmount())
        .cycleStart(balance.getCycleStart())
        .cycleEnd(balance.getCycleEnd())
        .status(balance.getStatus())
        .lastProcessedTx(balance.getLastProcessedTx())
        .attemptCount(balance.getAttemptCount())
        .lastNotifiedAt(balance.getLastNotifiedAt())
        .updatedAt(balance.getUpdatedAt())
        .build();
  }
}
