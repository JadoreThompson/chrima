package com.chrima.transaction.service;

import com.chrima.transaction.api.enums.TransactionStatus;
import com.chrima.transaction.model.Transaction;
import com.chrima.transaction.repository.TransactionRepository;
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
@Import(TransactionService.class)
public abstract class AbstractTransactionServiceIntegrationBase {

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

  @Autowired protected TransactionService transactionService;

  @Autowired protected TransactionRepository transactionRepository;

  @Autowired protected JdbcTemplate jdbcTemplate;

  @AfterEach
  void tearDown() {
    transactionRepository.deleteAll();
  }

  protected UUID createTransaction(
      UUID productId,
      UUID priceId,
      String sender,
      double amount,
      TransactionStatus status,
      int timestamp) {
    Transaction saved =
        transactionRepository.save(
            Transaction.builder()
                .productId(productId)
                .priceId(priceId)
                .platformUserId("platform-user")
                .sender(sender)
                .recipient("recipient")
                .address(sender)
                .amount(amount)
                .status(status)
                .timestamp(timestamp)
                .build());
    return saved.getId();
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
}
