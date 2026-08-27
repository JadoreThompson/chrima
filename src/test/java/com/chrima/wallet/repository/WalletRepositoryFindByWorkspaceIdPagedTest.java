package com.chrima.wallet.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.wallet.model.Wallet;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

@DataJpaTest
class WalletRepositoryFindByWorkspaceIdPagedTest {

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

  @Test
  void findByWorkspaceIdPagedShouldPaginateWithPageable() {
    UUID workspaceId = UUID.randomUUID();
    for (int i = 0; i < 3; i++) {
      createWallet(workspaceId, "wallet-" + i, "0x" + i);
    }

    var firstPage = walletRepository.findByWorkspaceId(workspaceId, PageRequest.of(0, 3));
    var page1 = walletRepository.findByWorkspaceId(workspaceId, PageRequest.of(0, 2));
    var page2 = walletRepository.findByWorkspaceId(workspaceId, PageRequest.of(1, 2));

    assertThat(firstPage.getContent()).hasSize(3);
    assertThat(firstPage.getTotalElements()).isEqualTo(3);
    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }
}
