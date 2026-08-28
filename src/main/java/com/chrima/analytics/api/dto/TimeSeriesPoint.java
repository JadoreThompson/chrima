package com.chrima.analytics.api.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class TimeSeriesPoint {
  String label;
  double value;

  /**
   * Creates a single time-series data point.
   *
   * @param label bucket label (e.g. "00:00", "Monday", "Week 1")
   * @param value aggregated value for the bucket
   * @return a new {@link TimeSeriesPoint}
   */
  public static TimeSeriesPoint from(String label, double value) {
    return TimeSeriesPoint.builder().label(label).value(value).build();
  }
}
