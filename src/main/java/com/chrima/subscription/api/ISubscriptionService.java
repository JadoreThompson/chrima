package com.chrima.subscription.api;

import com.chrima.price.api.enums.RecurringInterval;
import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import java.util.List;
import java.util.UUID;

public interface ISubscriptionService {

  SubscriptionBalanceResponse get(String externalId, String platformUserId, UUID productId);

  SubscriptionBalanceResponse getById(UUID subscriptionBalanceId);

  List<SubscriptionBalanceResponse> listByUserGroup(long userId, long externalId);

  SubscriptionBalanceResponse create(
      String externalId,
      String platformUserId,
      UUID productId,
      double creditAmount,
      SubscriptionStatus status,
      Integer cycleStart,
      Integer cycleEnd,
      UUID lastProcessedTx);

  SubscriptionBalanceResponse increaseBalance(
      String externalId, String platformUserId, UUID productId, double amount, UUID transactionId);

  SubscriptionBalanceResponse processCycle(
      String externalId,
      String platformUserId,
      UUID productId,
      double amount,
      RecurringInterval recurringInterval,
      int recurringIntervalCount,
      UUID transactionId);

  SubscriptionBalanceResponse cancel(UUID subscriptionBalanceId);
}
