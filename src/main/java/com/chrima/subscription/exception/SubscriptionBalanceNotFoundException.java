package com.chrima.subscription.exception;

import java.util.UUID;

public class SubscriptionBalanceNotFoundException extends RuntimeException {

  private final String externalId;
  private final String platformUserId;
  private final UUID productId;
  private final UUID balanceId;

  public SubscriptionBalanceNotFoundException(
      String externalId, String platformUserId, UUID productId) {
    super("Subscription balance not found");
    this.externalId = externalId;
    this.platformUserId = platformUserId;
    this.productId = productId;
    this.balanceId = null;
  }

  public SubscriptionBalanceNotFoundException(UUID balanceId) {
    super("Subscription balance not found");
    this.externalId = null;
    this.platformUserId = null;
    this.productId = null;
    this.balanceId = balanceId;
  }

  public String getExternalId() {
    return externalId;
  }

  public String getPlatformUserId() {
    return platformUserId;
  }

  public UUID getProductId() {
    return productId;
  }

  public UUID getBalanceId() {
    return balanceId;
  }
}
