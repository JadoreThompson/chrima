package com.chrima.analytics.controller;

import com.chrima.analytics.api.IAnalyticsService;
import com.chrima.analytics.api.dto.AnalyticsSummary;
import com.chrima.analytics.api.dto.AnalyticsTimeSeries;
import com.chrima.analytics.api.dto.SubscriptionAnalytics;
import com.chrima.analytics.api.enums.TimePeriod;
import com.chrima.jwt.api.IJwtService;
import com.chrima.workspace.api.IWorkspaceService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/analytics")
@RequiredArgsConstructor
public class AnalyticsController {

  private final IAnalyticsService analyticsService;
  private final IWorkspaceService workspaceService;
  private final IJwtService jwtService;

  /**
   * Returns aggregated totals for a workspace.
   *
   * @param workspaceId workspace to aggregate
   * @param token JWT cookie
   * @return summary totals
   */
  @GetMapping("/summary")
  public ResponseEntity<AnalyticsSummary> getSummary(
      @RequestParam UUID workspaceId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    Jwt jwt = jwtService.validate(token);
    workspaceService.get(workspaceId, UUID.fromString(jwt.getSubject()));
    AnalyticsSummary summary = analyticsService.getSummary(workspaceId);
    return ResponseEntity.ok(summary);
  }

  /**
   * Returns revenue bucketed by period.
   *
   * @param workspaceId workspace to aggregate
   * @param period raw period string (today, this_week, this_month)
   * @param token JWT cookie
   * @return revenue time-series
   */
  @GetMapping("/revenue")
  public ResponseEntity<AnalyticsTimeSeries> getRevenueTimeseries(
      @RequestParam UUID workspaceId,
      @RequestParam String period,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    Jwt jwt = jwtService.validate(token);
    workspaceService.get(workspaceId, UUID.fromString(jwt.getSubject()));
    TimePeriod timePeriod = TimePeriod.fromValue(period);
    AnalyticsTimeSeries series = analyticsService.getRevenueTimeseries(workspaceId, timePeriod);
    return ResponseEntity.ok(series);
  }

  /**
   * Returns distinct active-customer counts bucketed by period.
   *
   * @param workspaceId workspace to aggregate
   * @param period raw period string
   * @param token JWT cookie
   * @return active-customer time-series
   */
  @GetMapping("/active-customers")
  public ResponseEntity<AnalyticsTimeSeries> getActiveCustomersTimeseries(
      @RequestParam UUID workspaceId,
      @RequestParam String period,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    Jwt jwt = jwtService.validate(token);
    workspaceService.get(workspaceId, UUID.fromString(jwt.getSubject()));
    TimePeriod timePeriod = TimePeriod.fromValue(period);
    AnalyticsTimeSeries series =
        analyticsService.getActiveCustomersTimeseries(workspaceId, timePeriod);
    return ResponseEntity.ok(series);
  }

  /**
   * Returns subscription status breakdown for a workspace.
   *
   * @param workspaceId workspace to aggregate
   * @param token JWT cookie
   * @return subscription counts
   */
  @GetMapping("/subscriptions")
  public ResponseEntity<SubscriptionAnalytics> getSubscriptionAnalytics(
      @RequestParam UUID workspaceId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    Jwt jwt = jwtService.validate(token);
    workspaceService.get(workspaceId, UUID.fromString(jwt.getSubject()));
    SubscriptionAnalytics analytics = analyticsService.getSubscriptionBreakdown(workspaceId);
    return ResponseEntity.ok(analytics);
  }
}
