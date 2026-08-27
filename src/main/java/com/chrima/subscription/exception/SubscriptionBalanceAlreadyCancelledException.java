package com.chrima.subscription.exception;

import java.util.UUID;

public class SubscriptionBalanceAlreadyCancelledException extends RuntimeException {

  private final UUID balanceId;

  public SubscriptionBalanceAlreadyCancelledException(UUID balanceId) {
    super("Subscription balance " + balanceId + " is already cancelled");
    this.balanceId = balanceId;
  }

  public UUID getBalanceId() {
    return balanceId;
  }
}
