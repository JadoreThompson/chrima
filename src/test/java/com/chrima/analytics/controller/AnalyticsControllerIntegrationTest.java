package com.chrima.analytics.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.chrima.jwt.config.JwtProperties;
import com.chrima.user.model.User;
import com.chrima.user.repository.UserRepository;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.repository.WorkspaceRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.Cookie;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
class AnalyticsControllerIntegrationTest {

  @Container
  static PostgreSQLContainer<?> postgres =
      new PostgreSQLContainer<>("postgres:16-alpine")
          .withDatabaseName("chrima")
          .withUsername("postgres")
          .withPassword("password");

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
    registry.add("spring.datasource.driver-class-name", postgres::getDriverClassName);
  }

  @Autowired MockMvc mockMvc;
  @Autowired ObjectMapper objectMapper;
  @Autowired JwtProperties jwtProperties;
  @Autowired UserRepository userRepository;
  @Autowired WorkspaceRepository workspaceRepository;

  @Autowired com.chrima.jwt.api.IJwtService jwtService;

  private User user;
  private Workspace workspace;
  private Cookie authCookie;

  @BeforeEach
  void setUp() {
    workspaceRepository.deleteAll();
    userRepository.deleteAll();

    user =
        userRepository.save(
            User.builder()
                .username("analytics-user")
                .email("analytics@test.com")
                .password("hash")
                .build());

    workspace =
        workspaceRepository.save(
            Workspace.builder()
                .userId(user.getId())
                .name("analytics-ws")
                .platform(com.chrima.workspace.api.enums.MessagePlatformType.DISCORD)
                .externalId("ext-" + UUID.randomUUID())
                .notificationChannelId("channel-1")
                .build());

    String token = jwtService.encode(user.getId(), user.getEmail(), workspace.getId());
    user.setJwtToken(token);
    userRepository.save(user);
    authCookie = new Cookie(jwtProperties.getCookieAlias(), token);
  }

  @Test
  void shouldReturnSummaryWhenAuthenticated() throws Exception {
    mockMvc
        .perform(
            get("/analytics/summary")
                .param("workspaceId", workspace.getId().toString())
                .cookie(authCookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.totalRevenue").exists())
        .andExpect(jsonPath("$.totalActiveCustomers").exists())
        .andExpect(jsonPath("$.totalTransactions").exists());
  }

  @Test
  void shouldReturn401WithoutAuthForSummary() throws Exception {
    mockMvc
        .perform(get("/analytics/summary").param("workspaceId", workspace.getId().toString()))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturn404WhenWorkspaceNotOwned() throws Exception {
    UUID otherWorkspaceId = UUID.randomUUID();
    mockMvc
        .perform(
            get("/analytics/summary")
                .param("workspaceId", otherWorkspaceId.toString())
                .cookie(authCookie))
        .andExpect(status().isNotFound());
  }

  @Test
  void shouldReturnRevenueTimeseriesForToday() throws Exception {
    mockMvc
        .perform(
            get("/analytics/revenue")
                .param("workspaceId", workspace.getId().toString())
                .param("period", "today")
                .cookie(authCookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.period").value("TODAY"))
        .andExpect(jsonPath("$.points").isArray())
        .andExpect(jsonPath("$.points.length()").value(3));
  }

  @Test
  void shouldReturnRevenueTimeseriesForThisWeek() throws Exception {
    mockMvc
        .perform(
            get("/analytics/revenue")
                .param("workspaceId", workspace.getId().toString())
                .param("period", "this_week")
                .cookie(authCookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.period").value("THIS_WEEK"))
        .andExpect(jsonPath("$.points.length()").value(7));
  }

  @Test
  void shouldReturnRevenueTimeseriesForThisMonth() throws Exception {
    mockMvc
        .perform(
            get("/analytics/revenue")
                .param("workspaceId", workspace.getId().toString())
                .param("period", "this_month")
                .cookie(authCookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.period").value("THIS_MONTH"))
        .andExpect(jsonPath("$.points.length()").value(4));
  }

  @Test
  void shouldReturn400ForInvalidPeriod() throws Exception {
    mockMvc
        .perform(
            get("/analytics/revenue")
                .param("workspaceId", workspace.getId().toString())
                .param("period", "invalid")
                .cookie(authCookie))
        .andExpect(status().isBadRequest());
  }

  @Test
  void shouldReturn401WithoutAuthForRevenue() throws Exception {
    mockMvc
        .perform(
            get("/analytics/revenue")
                .param("workspaceId", workspace.getId().toString())
                .param("period", "today"))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturnActiveCustomersTimeseries() throws Exception {
    mockMvc
        .perform(
            get("/analytics/active-customers")
                .param("workspaceId", workspace.getId().toString())
                .param("period", "today")
                .cookie(authCookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.period").value("TODAY"))
        .andExpect(jsonPath("$.points.length()").value(3));
  }

  @Test
  void shouldReturn401WithoutAuthForActiveCustomers() throws Exception {
    mockMvc
        .perform(
            get("/analytics/active-customers")
                .param("workspaceId", workspace.getId().toString())
                .param("period", "today"))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturnSubscriptionAnalytics() throws Exception {
    mockMvc
        .perform(
            get("/analytics/subscriptions")
                .param("workspaceId", workspace.getId().toString())
                .cookie(authCookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.active").exists())
        .andExpect(jsonPath("$.expired").exists())
        .andExpect(jsonPath("$.cancelled").exists())
        .andExpect(jsonPath("$.expiring").exists());
  }

  @Test
  void shouldReturn401WithoutAuthForSubscriptions() throws Exception {
    mockMvc
        .perform(get("/analytics/subscriptions").param("workspaceId", workspace.getId().toString()))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturn400ForMissingWorkspaceId() throws Exception {
    mockMvc
        .perform(get("/analytics/summary").cookie(authCookie))
        .andExpect(status().isBadRequest());
  }
}
