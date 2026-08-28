package com.chrima.analytics.service;

import com.chrima.subscription.api.enums.SubscriptionStatus;
import com.chrima.subscription.model.SubscriptionBalance;
import com.chrima.subscription.repository.SubscriptionBalanceRepository;
import com.chrima.transaction.api.enums.TransactionStatus;
import com.chrima.transaction.model.Transaction;
import com.chrima.transaction.repository.TransactionRepository;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

@DataJpaTest
@Import(AnalyticsService.class)
public abstract class AbstractAnalyticsServiceIntegrationBase {

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

  @Autowired protected AnalyticsService analyticsService;

  @Autowired protected TransactionRepository transactionRepository;

  @Autowired protected SubscriptionBalanceRepository subscriptionBalanceRepository;

  @Autowired protected JdbcTemplate jdbcTemplate;

  @AfterEach
  void tearDown() {
    transactionRepository.deleteAll();
    subscriptionBalanceRepository.deleteAll();
    jdbcTemplate.execute("delete from prices");
    jdbcTemplate.execute("delete from products");
  }

  protected UUID createProduct(UUID workspaceId) {
    UUID productId = UUID.randomUUID();
    UUID walletId = UUID.randomUUID();
    jdbcTemplate.update(
        "insert into products (id, workspace_id, name, wallet_id, fulfilment_type, created_at, updated_at)"
            + " values (?, ?, ?, ?, ?, now(), now())",
        productId,
        workspaceId,
        "product-" + productId.toString().substring(0, 8),
        walletId,
        "INVITE");
    return productId;
  }

  protected UUID createPrice(UUID workspaceId, UUID productId) {
    UUID priceId = UUID.randomUUID();
    jdbcTemplate.update(
        "insert into prices (id, workspace_id, product_id, type, currency, amount, created_at, updated_at)"
            + " values (?, ?, ?, ?, ?, ?, now(), now())",
        priceId,
        workspaceId,
        productId,
        "ONE_TIME",
        "USD",
        10.0);
    return priceId;
  }

  protected UUID createTransaction(
      UUID productId,
      UUID priceId,
      String platformUserId,
      String sender,
      double amount,
      TransactionStatus status,
      int timestamp) {
    Transaction saved =
        transactionRepository.save(
            Transaction.builder()
                .productId(productId)
                .priceId(priceId)
                .platformUserId(platformUserId)
                .sender(sender)
                .recipient("recipient")
                .address(sender)
                .amount(amount)
                .status(status)
                .timestamp(timestamp)
                .build());
    return saved.getId();
  }

  protected UUID createSubscription(
      String externalId,
      String platformUserId,
      UUID productId,
      SubscriptionStatus status,
      Integer cycleStart,
      Integer cycleEnd) {
    SubscriptionBalance saved =
        subscriptionBalanceRepository.save(
            SubscriptionBalance.builder()
                .externalId(externalId)
                .platformUserId(platformUserId)
                .productId(productId)
                .creditAmount(100.0)
                .status(status)
                .cycleStart(cycleStart)
                .cycleEnd(cycleEnd)
                .build());
    return saved.getId();
  }

  protected int epochOf(ZonedDateTime dt) {
    return (int) dt.toEpochSecond();
  }

  protected ZonedDateTime nowUtc() {
    return ZonedDateTime.now(ZoneOffset.UTC);
  }

  protected ZonedDateTime todayStartUtc() {
    return nowUtc().toLocalDate().atStartOfDay(ZoneOffset.UTC);
  }

  protected ZonedDateTime weekStartUtc() {
    ZonedDateTime now = nowUtc();
    return now.minusDays(now.getDayOfWeek().getValue() - 1)
        .toLocalDate()
        .atStartOfDay(ZoneOffset.UTC);
  }

  protected ZonedDateTime monthStartUtc() {
    return nowUtc().withDayOfMonth(1).toLocalDate().atStartOfDay(ZoneOffset.UTC);
  }

  protected long nowEpoch() {
    return Instant.now().getEpochSecond();
  }
}
