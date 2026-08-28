package com.chrima.analytics.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.analytics.api.dto.AnalyticsTimeSeries;
import com.chrima.analytics.api.enums.TimePeriod;
import com.chrima.transaction.api.enums.TransactionStatus;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class AnalyticsServiceGetActiveCustomersTimeseriesTest
    extends AbstractAnalyticsServiceIntegrationBase {

  @Test
  void shouldReturnZeroPointsWhenNoTransactions() {
    UUID workspaceId = UUID.randomUUID();

    AnalyticsTimeSeries series =
        analyticsService.getActiveCustomersTimeseries(workspaceId, TimePeriod.TODAY);

    assertThat(series.getPeriod()).isEqualTo(TimePeriod.TODAY);
    assertThat(series.getPoints()).hasSize(3);
    assertThat(series.getPoints()).allMatch(p -> p.getValue() == 0.0);
  }

  @Test
  void shouldCountDistinctCustomersPerBucketToday() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    int tsMorning = epochOf(todayStartUtc().plusHours(1)); // bucket 0
    int tsMidday = epochOf(todayStartUtc().plusHours(9)); // bucket 1

    // same platform user twice in same bucket should count once
    createTransaction(
        productId, priceId, "user-a", "0xsender", 10.0, TransactionStatus.COMPLETE, tsMorning);
    createTransaction(
        productId, priceId, "user-a", "0xsender", 15.0, TransactionStatus.COMPLETE, tsMorning);
    createTransaction(
        productId, priceId, "user-b", "0xsender", 20.0, TransactionStatus.COMPLETE, tsMorning);
    createTransaction(
        productId, priceId, "user-c", "0xsender", 5.0, TransactionStatus.COMPLETE, tsMidday);
    // failed should be ignored
    createTransaction(
        productId, priceId, "user-d", "0xsender", 999.0, TransactionStatus.FAILED, tsMorning);

    AnalyticsTimeSeries series =
        analyticsService.getActiveCustomersTimeseries(workspaceId, TimePeriod.TODAY);

    assertThat(series.getPoints().get(0).getValue()).isEqualTo(2.0); // user-a, user-b
    assertThat(series.getPoints().get(1).getValue()).isEqualTo(1.0); // user-c
    assertThat(series.getPoints().get(2).getValue()).isZero();
  }

  @Test
  void shouldCountDistinctCustomersPerBucketWeek() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    int tsMonday = epochOf(weekStartUtc().plusHours(1));
    int tsTuesday = epochOf(weekStartUtc().plusDays(1).plusHours(1));

    createTransaction(
        productId, priceId, "user-1", "0xsender", 10.0, TransactionStatus.COMPLETE, tsMonday);
    createTransaction(
        productId, priceId, "user-2", "0xsender", 10.0, TransactionStatus.COMPLETE, tsMonday);
    createTransaction(
        productId, priceId, "user-1", "0xsender", 10.0, TransactionStatus.COMPLETE, tsTuesday);

    AnalyticsTimeSeries series =
        analyticsService.getActiveCustomersTimeseries(workspaceId, TimePeriod.THIS_WEEK);

    assertThat(series.getPoints()).hasSize(7);
    assertThat(series.getPoints().get(0).getValue()).isEqualTo(2.0);
    assertThat(series.getPoints().get(1).getValue()).isEqualTo(1.0);
    assertThat(series.getPoints().get(2).getValue()).isZero();
  }

  @Test
  void shouldCountDistinctCustomersPerBucketMonth() {
    UUID workspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    int tsWeek1 = epochOf(monthStartUtc().plusDays(1).plusHours(1));
    int tsWeek4a = epochOf(monthStartUtc().plusDays(22).plusHours(1));
    int tsWeek4b = epochOf(monthStartUtc().plusDays(27).plusHours(1));

    createTransaction(
        productId, priceId, "user-x", "0xsender", 10.0, TransactionStatus.COMPLETE, tsWeek1);
    createTransaction(
        productId, priceId, "user-y", "0xsender", 10.0, TransactionStatus.COMPLETE, tsWeek4a);
    createTransaction(
        productId, priceId, "user-y", "0xsender", 10.0, TransactionStatus.COMPLETE, tsWeek4b);
    createTransaction(
        productId, priceId, "user-z", "0xsender", 10.0, TransactionStatus.COMPLETE, tsWeek4b);

    AnalyticsTimeSeries series =
        analyticsService.getActiveCustomersTimeseries(workspaceId, TimePeriod.THIS_MONTH);

    assertThat(series.getPoints().get(0).getValue()).isEqualTo(1.0);
    assertThat(series.getPoints().get(3).getValue()).isEqualTo(2.0); // user-y and user-z in Week 4
  }

  @Test
  void shouldIgnoreOtherWorkspaceCustomers() {
    UUID workspaceId = UUID.randomUUID();
    UUID otherWorkspaceId = UUID.randomUUID();
    UUID productId = createProduct(workspaceId);
    UUID otherProductId = createProduct(otherWorkspaceId);
    UUID priceId = createPrice(workspaceId, productId);
    UUID otherPriceId = createPrice(otherWorkspaceId, otherProductId);
    int ts = epochOf(todayStartUtc().plusHours(2));

    createTransaction(
        productId, priceId, "user-1", "0xsender", 10.0, TransactionStatus.COMPLETE, ts);
    createTransaction(
        otherProductId, otherPriceId, "user-2", "0xsender", 10.0, TransactionStatus.COMPLETE, ts);

    AnalyticsTimeSeries series =
        analyticsService.getActiveCustomersTimeseries(workspaceId, TimePeriod.TODAY);

    assertThat(series.getPoints().get(0).getValue()).isEqualTo(1.0);
    assertThat(series.getPoints().get(1).getValue()).isZero();
  }
}
