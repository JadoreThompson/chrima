package com.chrima.analytics.api;

import com.chrima.analytics.api.dto.AnalyticsSummary;
import com.chrima.analytics.api.dto.AnalyticsTimeSeries;
import com.chrima.analytics.api.dto.SubscriptionAnalytics;
import com.chrima.analytics.api.enums.TimePeriod;
import java.util.UUID;

public interface IAnalyticsService {

  /**
   * Returns high-level totals for a workspace.
   *
   * @param workspaceId owning workspace
   * @return summary totals
   */
  AnalyticsSummary getSummary(UUID workspaceId);

  /**
   * Returns revenue bucketed by the given period.
   *
   * @param workspaceId owning workspace
   * @param period bucketing period
   * @return time-series of summed revenue
   */
  AnalyticsTimeSeries getRevenueTimeseries(UUID workspaceId, TimePeriod period);

  /**
   * Returns distinct active-customer counts bucketed by the given period.
   *
   * @param workspaceId owning workspace
   * @param period bucketing period
   * @return time-series of active-customer counts
   */
  AnalyticsTimeSeries getActiveCustomersTimeseries(UUID workspaceId, TimePeriod period);

  /**
   * Returns counts of subscriptions by status for a workspace.
   *
   * @param workspaceId owning workspace
   * @return breakdown by status
   */
  SubscriptionAnalytics getSubscriptionBreakdown(UUID workspaceId);
}
