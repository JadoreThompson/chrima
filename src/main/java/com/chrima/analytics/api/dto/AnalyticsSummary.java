package com.chrima.analytics.api.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class AnalyticsSummary {
  double totalRevenue;
  long totalActiveCustomers;
  long totalTransactions;

  /**
   * Creates a summary DTO from aggregated values.
   *
   * @param totalRevenue total completed revenue for the workspace
   * @param totalActiveCustomers number of distinct customers with an ACTIVE subscription
   * @param totalTransactions number of COMPLETE transactions
   * @return a new {@link AnalyticsSummary}
   */
  public static AnalyticsSummary from(
      double totalRevenue, long totalActiveCustomers, long totalTransactions) {
    return AnalyticsSummary.builder()
        .totalRevenue(totalRevenue)
        .totalActiveCustomers(totalActiveCustomers)
        .totalTransactions(totalTransactions)
        .build();
  }
}
