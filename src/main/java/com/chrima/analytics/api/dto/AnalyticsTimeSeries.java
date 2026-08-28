package com.chrima.analytics.api.dto;

import com.chrima.analytics.api.enums.TimePeriod;
import java.util.List;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class AnalyticsTimeSeries {
  TimePeriod period;
  List<TimeSeriesPoint> points;

  /**
   * Creates a time-series response for the given period.
   *
   * @param period the requested period
   * @param points bucketed points in period order
   * @return a new {@link AnalyticsTimeSeries}
   */
  public static AnalyticsTimeSeries from(TimePeriod period, List<TimeSeriesPoint> points) {
    return AnalyticsTimeSeries.builder().period(period).points(points).build();
  }
}
