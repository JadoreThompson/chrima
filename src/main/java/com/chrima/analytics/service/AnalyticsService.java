package com.chrima.analytics.service;

import com.chrima.analytics.api.IAnalyticsService;
import com.chrima.analytics.api.dto.AnalyticsSummary;
import com.chrima.analytics.api.dto.AnalyticsTimeSeries;
import com.chrima.analytics.api.dto.SubscriptionAnalytics;
import com.chrima.analytics.api.dto.TimeSeriesPoint;
import com.chrima.analytics.api.enums.TimePeriod;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.transaction.api.enums.TransactionStatus;
import jakarta.persistence.EntityManager;
import java.time.DayOfWeek;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.time.format.TextStyle;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AnalyticsService implements IAnalyticsService {

  private final EntityManager entityManager;

  @Override
  @Transactional(readOnly = true)
  public AnalyticsSummary getSummary(UUID workspaceId) {
    double totalRevenue = queryTotalRevenue(workspaceId);
    long totalActiveCustomers = queryTotalActiveCustomers(workspaceId);
    long totalTransactions = queryTotalTransactions(workspaceId);
    return AnalyticsSummary.from(totalRevenue, totalActiveCustomers, totalTransactions);
  }

  @Override
  @Transactional(readOnly = true)
  public AnalyticsTimeSeries getRevenueTimeseries(UUID workspaceId, TimePeriod period) {
    PeriodBounds bounds = periodBounds(period);
    Map<Integer, Double> bucketMap = queryRevenueBuckets(workspaceId, bounds, period);
    List<TimeSeriesPoint> points = new ArrayList<>();
    for (Map.Entry<Integer, String> entry : bounds.labels().entrySet()) {
      double value = bucketMap.getOrDefault(entry.getKey(), 0.0);
      points.add(TimeSeriesPoint.from(entry.getValue(), value));
    }
    return AnalyticsTimeSeries.from(period, points);
  }

  @Override
  @Transactional(readOnly = true)
  public AnalyticsTimeSeries getActiveCustomersTimeseries(UUID workspaceId, TimePeriod period) {
    PeriodBounds bounds = periodBounds(period);
    Map<Integer, Set<String>> bucketCustomers =
        queryActiveCustomersBuckets(workspaceId, bounds, period);
    List<TimeSeriesPoint> points = new ArrayList<>();
    for (Map.Entry<Integer, String> entry : bounds.labels().entrySet()) {
      Set<String> customers = bucketCustomers.getOrDefault(entry.getKey(), Set.of());
      points.add(TimeSeriesPoint.from(entry.getValue(), (double) customers.size()));
    }
    return AnalyticsTimeSeries.from(period, points);
  }

  @Override
  @Transactional(readOnly = true)
  public SubscriptionAnalytics getSubscriptionBreakdown(UUID workspaceId) {
    long now = Instant.now().getEpochSecond();
    long expiringThreshold = now + 7 * 86400L;

    String sql =
        """
        SELECT
          COALESCE(SUM(CASE WHEN b.status = :active THEN 1 ELSE 0 END), 0),
          COALESCE(SUM(CASE WHEN b.status = :expired THEN 1 ELSE 0 END), 0),
          COALESCE(SUM(CASE WHEN b.status = :cancelled THEN 1 ELSE 0 END), 0),
          COALESCE(SUM(CASE WHEN b.status = :active AND b.cycle_end IS NOT NULL AND b.cycle_end <= :threshold THEN 1 ELSE 0 END), 0)
        FROM subscription_balances b
        JOIN products p ON p.id = b.product_id
        WHERE p.workspace_id = :workspaceId
        """;

    Object[] row =
        (Object[])
            entityManager
                .createNativeQuery(sql)
                .setParameter("active", SubscriptionStatus.ACTIVE.name())
                .setParameter("expired", SubscriptionStatus.EXPIRED.name())
                .setParameter("cancelled", SubscriptionStatus.CANCELLED.name())
                .setParameter("threshold", expiringThreshold)
                .setParameter("workspaceId", workspaceId)
                .getSingleResult();

    long active = ((Number) row[0]).longValue();
    long expired = ((Number) row[1]).longValue();
    long cancelled = ((Number) row[2]).longValue();
    long expiring = ((Number) row[3]).longValue();

    return SubscriptionAnalytics.from(active, expired, cancelled, expiring);
  }

  private double queryTotalRevenue(UUID workspaceId) {
    String sql =
        """
        SELECT COALESCE(SUM(t.amount), 0)
        FROM transactions t
        JOIN prices p ON p.id = t.price_id
        WHERE p.workspace_id = :workspaceId
          AND t.status = :status
        """;
    Object result =
        entityManager
            .createNativeQuery(sql)
            .setParameter("workspaceId", workspaceId)
            .setParameter("status", TransactionStatus.COMPLETE.name())
            .getSingleResult();
    return ((Number) result).doubleValue();
  }

  private long queryTotalActiveCustomers(UUID workspaceId) {
    String sql =
        """
        SELECT COUNT(DISTINCT b.platform_user_id)
        FROM subscription_balances b
        JOIN products p ON p.id = b.product_id
        WHERE p.workspace_id = :workspaceId
          AND b.status = :status
        """;
    Object result =
        entityManager
            .createNativeQuery(sql)
            .setParameter("workspaceId", workspaceId)
            .setParameter("status", SubscriptionStatus.ACTIVE.name())
            .getSingleResult();
    return ((Number) result).longValue();
  }

  private long queryTotalTransactions(UUID workspaceId) {
    String sql =
        """
        SELECT COUNT(t.id)
        FROM transactions t
        JOIN prices p ON p.id = t.price_id
        WHERE p.workspace_id = :workspaceId
          AND t.status = :status
        """;
    Object result =
        entityManager
            .createNativeQuery(sql)
            .setParameter("workspaceId", workspaceId)
            .setParameter("status", TransactionStatus.COMPLETE.name())
            .getSingleResult();
    return ((Number) result).longValue();
  }

  private Map<Integer, Double> queryRevenueBuckets(
      UUID workspaceId, PeriodBounds bounds, TimePeriod period) {
    List<Object[]> rows = queryTransactionRows(workspaceId, bounds);
    Map<Integer, Double> map = new HashMap<>();
    for (Object[] row : rows) {
      int ts = ((Number) row[0]).intValue();
      double amount = ((Number) row[1]).doubleValue();
      int bucket = bucketFor(period, ts);
      map.merge(bucket, amount, Double::sum);
    }
    return map;
  }

  private Map<Integer, Set<String>> queryActiveCustomersBuckets(
      UUID workspaceId, PeriodBounds bounds, TimePeriod period) {
    List<Object[]> rows = queryTransactionCustomerRows(workspaceId, bounds);
    Map<Integer, Set<String>> map = new HashMap<>();
    for (Object[] row : rows) {
      int ts = ((Number) row[0]).intValue();
      String platformUserId = (String) row[1];
      int bucket = bucketFor(period, ts);
      map.computeIfAbsent(bucket, k -> new HashSet<>()).add(platformUserId);
    }
    return map;
  }

  @SuppressWarnings("unchecked")
  private List<Object[]> queryTransactionRows(UUID workspaceId, PeriodBounds bounds) {
    String sql =
        """
        SELECT t.timestamp, t.amount
        FROM transactions t
        JOIN prices p ON p.id = t.price_id
        WHERE p.workspace_id = :workspaceId
          AND t.status = :status
          AND t.timestamp >= :start
          AND t.timestamp < :end
        """;
    return entityManager
        .createNativeQuery(sql)
        .setParameter("workspaceId", workspaceId)
        .setParameter("status", TransactionStatus.COMPLETE.name())
        .setParameter("start", (int) bounds.start())
        .setParameter("end", (int) bounds.end())
        .getResultList();
  }

  @SuppressWarnings("unchecked")
  private List<Object[]> queryTransactionCustomerRows(UUID workspaceId, PeriodBounds bounds) {
    String sql =
        """
        SELECT t.timestamp, t.platform_user_id
        FROM transactions t
        JOIN prices p ON p.id = t.price_id
        WHERE p.workspace_id = :workspaceId
          AND t.status = :status
          AND t.timestamp >= :start
          AND t.timestamp < :end
        """;
    return entityManager
        .createNativeQuery(sql)
        .setParameter("workspaceId", workspaceId)
        .setParameter("status", TransactionStatus.COMPLETE.name())
        .setParameter("start", (int) bounds.start())
        .setParameter("end", (int) bounds.end())
        .getResultList();
  }

  private int bucketFor(TimePeriod period, int timestamp) {
    ZonedDateTime dt = Instant.ofEpochSecond(timestamp).atZone(ZoneOffset.UTC);
    return switch (period) {
      case TODAY -> dt.getHour() / 8;
      case THIS_WEEK -> {
        DayOfWeek dow = dt.getDayOfWeek();
        // Monday 0 ... Sunday 6  -> (dow.getValue()+6)%7 gives same
        yield (dow.getValue() + 6) % 7;
      }
      case THIS_MONTH -> Math.min((dt.getDayOfMonth() - 1) / 7, 3);
    };
  }

  private PeriodBounds periodBounds(TimePeriod period) {
    ZonedDateTime now = ZonedDateTime.now(ZoneOffset.UTC);
    long end = now.toEpochSecond();

    if (period == TimePeriod.TODAY) {
      ZonedDateTime startDt = now.toLocalDate().atStartOfDay(ZoneOffset.UTC);
      long start = startDt.toEpochSecond();
      Map<Integer, String> labels = new LinkedHashMap<>();
      labels.put(0, "00:00");
      labels.put(1, "08:00");
      labels.put(2, "16:00");
      return new PeriodBounds(start, end, labels);
    }

    if (period == TimePeriod.THIS_WEEK) {
      ZonedDateTime weekStart =
          now.minusDays(now.getDayOfWeek().getValue() - DayOfWeek.MONDAY.getValue())
              .toLocalDate()
              .atStartOfDay(ZoneOffset.UTC);
      long start = weekStart.toEpochSecond();
      Map<Integer, String> labels = new LinkedHashMap<>();
      for (int i = 0; i < 7; i++) {
        ZonedDateTime d = weekStart.plusDays(i);
        String label = d.getDayOfWeek().getDisplayName(TextStyle.FULL, Locale.ENGLISH);
        labels.put(i, label);
      }
      return new PeriodBounds(start, end, labels);
    }

    if (period == TimePeriod.THIS_MONTH) {
      ZonedDateTime monthStart = now.withDayOfMonth(1).toLocalDate().atStartOfDay(ZoneOffset.UTC);
      long start = monthStart.toEpochSecond();
      Map<Integer, String> labels = new LinkedHashMap<>();
      for (int i = 0; i < 4; i++) {
        labels.put(i, "Week " + (i + 1));
      }
      return new PeriodBounds(start, end, labels);
    }

    // Fallback mirrors Python's three-month path (unused with current enum but kept for parity)
    ZonedDateTime threeMonthsAgo =
        now.minusMonths(2).withDayOfMonth(1).toLocalDate().atStartOfDay(ZoneOffset.UTC);
    long start = threeMonthsAgo.toEpochSecond();
    Map<Integer, String> labels = new LinkedHashMap<>();
    for (int i = 0; i < 3; i++) {
      ZonedDateTime d = threeMonthsAgo.plusMonths(i);
      String label = d.getMonth().getDisplayName(TextStyle.FULL, Locale.ENGLISH);
      // bucket key is month number (1-12) to match original Python's month extract
      labels.put(d.getMonthValue(), label);
    }
    return new PeriodBounds(start, end, labels);
  }

  private record PeriodBounds(long start, long end, Map<Integer, String> labels) {}
}
