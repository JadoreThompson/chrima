package com.chrima.analytics.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.analytics.api.dto.AnalyticsTimeSeries;
import com.chrima.analytics.api.enums.TimePeriod;
import com.chrima.transaction.api.enums.TransactionStatus;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class AnalyticsServiceGetRevenueTimeseriesTest extends AbstractAnalyticsServiceIntegrationBase {

  @Test
  void shouldReturnZeroPointsWhenNoTransactions() {
    UUID workspaceId = UUID.randomUUID();

    AnalyticsTimeSeries series =
        analyticsService.getRevenueTimeseries(workspaceId, TimePeriod.TODAY);

    assertThat(series.getPeriod()).isEqualTo(TimePeriod.TODAY);
    assertThat(series.getPoints()).hasSize(3);
    assertThat(series.getPoints()).allMatch(p -> p.getValue() == 0.0);
    assertThat(series.getPoints().get(0).getLabel()).isEqualTo("00:00");
    assertThat(series.getPoints().get(1).getLabel()).isEqualTo("08:00");
    assertThat(series.getPoints().get(2).getLabel()).isEqualTo("16:00");
  }

  @Test
  void shouldBucketRevenueForToday() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    ZonedDateTime todayStart = todayStartUtc();
    ZonedDateTime now = nowUtc();
    int tsMorning = epochOf(todayStart.plusHours(1)); // bucket 0
    int tsMidday = epochOf(todayStart.plusHours(9)); // bucket 1
    int tsEvening = epochOf(todayStart.plusHours(17)); // bucket 2
    int tsBeforeToday = epochOf(todayStart.minusHours(1)); // should be ignored
    long nowEpoch = now.toEpochSecond();

    createTransaction(
        productId, priceId, "user-1", "0xsender", 10.0, TransactionStatus.COMPLETE, tsMorning);
    createTransaction(
        productId, priceId, "user-2", "0xsender", 20.0, TransactionStatus.COMPLETE, tsMorning);
    createTransaction(
        productId, priceId, "user-3", "0xsender", 5.0, TransactionStatus.COMPLETE, tsMidday);
    createTransaction(
        productId, priceId, "user-4", "0xsender", 15.0, TransactionStatus.COMPLETE, tsEvening);
    createTransaction(
        productId, priceId, "user-5", "0xsender", 999.0, TransactionStatus.COMPLETE, tsBeforeToday);
    createTransaction(
        productId, priceId, "user-6", "0xsender", 999.0, TransactionStatus.FAILED, tsMorning);

    AnalyticsTimeSeries series =
        analyticsService.getRevenueTimeseries(workspaceId, TimePeriod.TODAY);

    assertThat(series.getPeriod()).isEqualTo(TimePeriod.TODAY);
    assertThat(series.getPoints()).hasSize(3);
    // compute expected dynamically respecting timestamp < now filtering
    double bucket0 = 30.0;
    double bucket1 = (tsMidday < nowEpoch && tsMidday >= todayStart.toEpochSecond()) ? 5.0 : 0.0;
    double bucket2 = (tsEvening < nowEpoch && tsEvening >= todayStart.toEpochSecond()) ? 15.0 : 0.0;
    assertThat(series.getPoints().get(0).getValue()).isEqualTo(bucket0);
    assertThat(series.getPoints().get(1).getValue()).isEqualTo(bucket1);
    assertThat(series.getPoints().get(2).getValue()).isEqualTo(bucket2);
  }

  @Test
  void shouldBucketRevenueForThisWeek() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    ZonedDateTime weekStart = weekStartUtc(); // Monday
    ZonedDateTime now = nowUtc();
    long nowEpoch = now.toEpochSecond();
    long weekStartEpoch = weekStart.toEpochSecond();
    int tsMonday = epochOf(weekStart.plusHours(2));
    int tsWednesday = epochOf(weekStart.plusDays(2).plusHours(3));
    int tsSunday = epochOf(weekStart.plusDays(6).plusHours(1));

    createTransaction(
        productId, priceId, "user-1", "0xsender", 100.0, TransactionStatus.COMPLETE, tsMonday);
    createTransaction(
        productId, priceId, "user-2", "0xsender", 50.0, TransactionStatus.COMPLETE, tsWednesday);
    createTransaction(
        productId, priceId, "user-3", "0xsender", 25.0, TransactionStatus.COMPLETE, tsSunday);

    AnalyticsTimeSeries series =
        analyticsService.getRevenueTimeseries(workspaceId, TimePeriod.THIS_WEEK);

    assertThat(series.getPeriod()).isEqualTo(TimePeriod.THIS_WEEK);
    assertThat(series.getPoints()).hasSize(7);
    assertThat(series.getPoints().get(0).getLabel()).isEqualTo("Monday");
    double expectedMonday = (tsMonday >= weekStartEpoch && tsMonday < nowEpoch) ? 100.0 : 0.0;
    double expectedWednesday =
        (tsWednesday >= weekStartEpoch && tsWednesday < nowEpoch) ? 50.0 : 0.0;
    double expectedSunday = (tsSunday >= weekStartEpoch && tsSunday < nowEpoch) ? 25.0 : 0.0;
    assertThat(series.getPoints().get(0).getValue()).isEqualTo(expectedMonday);
    assertThat(series.getPoints().get(2).getValue()).isEqualTo(expectedWednesday);
    assertThat(series.getPoints().get(6).getValue()).isEqualTo(expectedSunday);
    // at least one mid-week bucket should be zero (e.g., index 1)
    assertThat(series.getPoints().get(1).getValue()).isZero();
  }

  @Test
  void shouldBucketRevenueForThisMonth() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    ZonedDateTime monthStart = monthStartUtc();
    int tsWeek1 = epochOf(monthStart.plusDays(0).plusHours(1)); // day 1 => bucket 0
    int tsWeek2 = epochOf(monthStart.plusDays(7).plusHours(1)); // day 8 => bucket 1
    int tsWeek3 = epochOf(monthStart.plusDays(14).plusHours(1)); // day 15 => bucket 2
    int tsWeek4 = epochOf(monthStart.plusDays(21).plusHours(1)); // day 22 => bucket 3
    int tsWeek4b = epochOf(monthStart.plusDays(27).plusHours(1)); // day 28 => bucket 3 capped

    createTransaction(
        productId, priceId, "user-1", "0xsender", 10.0, TransactionStatus.COMPLETE, tsWeek1);
    createTransaction(
        productId, priceId, "user-2", "0xsender", 20.0, TransactionStatus.COMPLETE, tsWeek2);
    createTransaction(
        productId, priceId, "user-3", "0xsender", 30.0, TransactionStatus.COMPLETE, tsWeek3);
    createTransaction(
        productId, priceId, "user-4", "0xsender", 40.0, TransactionStatus.COMPLETE, tsWeek4);
    createTransaction(
        productId, priceId, "user-5", "0xsender", 5.0, TransactionStatus.COMPLETE, tsWeek4b);

    AnalyticsTimeSeries series =
        analyticsService.getRevenueTimeseries(workspaceId, TimePeriod.THIS_MONTH);

    assertThat(series.getPeriod()).isEqualTo(TimePeriod.THIS_MONTH);
    assertThat(series.getPoints()).hasSize(4);
    assertThat(series.getPoints().get(0).getLabel()).isEqualTo("Week 1");
    assertThat(series.getPoints().get(0).getValue()).isEqualTo(10.0);
    assertThat(series.getPoints().get(1).getValue()).isEqualTo(20.0);
    assertThat(series.getPoints().get(2).getValue()).isEqualTo(30.0);
    // Week 4 bucket aggregates both day 22 and 28
    assertThat(series.getPoints().get(3).getValue()).isEqualTo(45.0);
  }

  @Test
  void shouldIgnoreFailedAndOtherWorkspaceTransactions() {
    UUID workspaceId = UUID.randomUUID();
    UUID otherWorkspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID otherProductId = createProduct(otherWorkspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    UUID otherPriceId = createPrice(otherWorkspaceId, otherProductId);
    ZonedDateTime todayStart = todayStartUtc();
    int ts = epochOf(todayStart.plusHours(2));

    createTransaction(productId, priceId, "user-1", "0xsender", 10.0, TransactionStatus.FAILED, ts);
    createTransaction(
        otherProductId, otherPriceId, "user-2", "0xsender", 999.0, TransactionStatus.COMPLETE, ts);

    AnalyticsTimeSeries series =
        analyticsService.getRevenueTimeseries(workspaceId, TimePeriod.TODAY);

    assertThat(series.getPoints()).allMatch(p -> p.getValue() == 0.0);
  }

  @Test
  void shouldIgnoreFutureTimestamp() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    int futureTs = (int) (ZonedDateTime.now(ZoneOffset.UTC).plusDays(1).toEpochSecond());

    createTransaction(
        productId, priceId, "user-1", "0xsender", 50.0, TransactionStatus.COMPLETE, futureTs);

    AnalyticsTimeSeries series =
        analyticsService.getRevenueTimeseries(workspaceId, TimePeriod.TODAY);

    assertThat(series.getPoints()).allMatch(p -> p.getValue() == 0.0);
  }
}
