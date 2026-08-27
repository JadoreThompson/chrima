package com.chrima.subscription.service;

import com.chrima.events.api.IEventService;
import com.chrima.subscription.api.dto.SubscriptionBalanceResponse;
import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.repository.SubscriptionBalanceRepository;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.testcontainers.containers.PostgreSQLContainer;

@DataJpaTest
@Import(SubscriptionBalanceService.class)
public abstract class AbstractSubscriptionServiceIntegrationBase {

  @SuppressWarnings("resource")
  static final PostgreSQLContainer<?> postgres =
      new PostgreSQLContainer<>("postgres:16-alpine")
          .withDatabaseName("chrima")
          .withUsername("postgres")
          .withPassword("password");

  static {
    postgres.start();
  }

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
    registry.add("spring.datasource.driver-class-name", postgres::getDriverClassName);
  }

  @Autowired protected SubscriptionBalanceService subscriptionService;

  @Autowired protected SubscriptionBalanceRepository subscriptionBalanceRepository;

  @MockitoBean protected IEventService eventService;

  @AfterEach
  void tearDown() {
    subscriptionBalanceRepository.deleteAll();
  }

  protected SubscriptionBalanceResponse createBalance(
      String externalId,
      String platformUserId,
      UUID productId,
      double creditAmount,
      SubscriptionStatus status) {
    return subscriptionService.create(
        externalId, platformUserId, productId, creditAmount, status, null, null, null);
  }
}
