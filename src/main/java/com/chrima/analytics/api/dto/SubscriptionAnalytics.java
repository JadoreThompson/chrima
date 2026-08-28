package com.chrima.analytics.api.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class SubscriptionAnalytics {
  long active;
  long expired;
  long cancelled;

  /** Active subscriptions whose cycleEnd is within the next 7 days. */
  long expiring;

  /**
   * Creates a subscription breakdown DTO.
   *
   * @param active count of ACTIVE
   * @param expired count of EXPIRED
   * @param cancelled count of CANCELLED
   * @param expiring count of ACTIVE with cycleEnd within 7 days
   * @return a new {@link SubscriptionAnalytics}
   */
  public static SubscriptionAnalytics from(
      long active, long expired, long cancelled, long expiring) {
    return SubscriptionAnalytics.builder()
        .active(active)
        .expired(expired)
        .cancelled(cancelled)
        .expiring(expiring)
        .build();
  }
}
