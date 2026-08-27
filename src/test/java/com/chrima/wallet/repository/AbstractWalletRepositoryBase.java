package com.chrima.wallet.repository;

import com.chrima.wallet.model.Wallet;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
public abstract class AbstractWalletRepositoryBase {

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

  @Autowired protected WalletRepository walletRepository;

  @Autowired protected WalletTokenRepository walletTokenRepository;

  @AfterEach
  void tearDown() {
    try {
      walletTokenRepository.deleteAll();
    } catch (Exception ignored) {
    }
    try {
      walletRepository.deleteAll();
    } catch (Exception ignored) {
    }
  }

  protected Wallet createWallet(UUID workspaceId, String name, String address) {
    Wallet wallet =
        Wallet.builder().workspaceId(workspaceId).name(name).walletAddress(address).build();
    return walletRepository.save(wallet);
  }

  protected Wallet createWalletWithWorkspace() {
    return createWallet(UUID.randomUUID(), "wallet", "0xabc");
  }
}
