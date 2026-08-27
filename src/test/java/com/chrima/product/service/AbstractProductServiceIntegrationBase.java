package com.chrima.product.service;

import com.chrima.product.repository.ProductRepository;
import com.chrima.user.config.PasswordEncoderConfig;
import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;
import com.chrima.user.repository.UserRepository;
import com.chrima.user.service.UserService;
import com.chrima.wallet.model.Wallet;
import com.chrima.wallet.repository.WalletRepository;
import com.chrima.wallet.repository.WalletTokenRepository;
import com.chrima.wallet.service.WalletService;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.model.enums.MessagePlatformType;
import com.chrima.workspace.repository.WorkspaceRepository;
import com.chrima.workspace.service.WorkspaceService;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

@DataJpaTest
@Import({
  ProductService.class,
  WalletService.class,
  WorkspaceService.class,
  UserService.class,
  PasswordEncoderConfig.class
})
public abstract class AbstractProductServiceIntegrationBase {

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

  @Autowired protected ProductService productService;

  @Autowired protected ProductRepository productRepository;

  @Autowired protected WalletService walletService;

  @Autowired protected WalletRepository walletRepository;

  @Autowired protected WalletTokenRepository walletTokenRepository;

  @Autowired protected WorkspaceRepository workspaceRepository;

  @Autowired protected UserRepository userRepository;

  @AfterEach
  void tearDown() {
    try {
      productRepository.deleteAll();
    } catch (Exception ignored) {
    }
    try {
      walletTokenRepository.deleteAll();
    } catch (Exception ignored) {
    }
    try {
      walletRepository.deleteAll();
    } catch (Exception ignored) {
    }
    try {
      workspaceRepository.deleteAll();
    } catch (Exception ignored) {
    }
    try {
      userRepository.deleteAll();
    } catch (Exception ignored) {
    }
  }

  protected User createUser() {
    User user =
        User.builder()
            .username("user-" + UUID.randomUUID().toString().substring(0, 8))
            .email(UUID.randomUUID() + "@example.com")
            .password("hashed")
            .tier(Tier.FREE)
            .build();
    return userRepository.save(user);
  }

  protected Workspace createWorkspace(UUID userId) {
    Workspace ws =
        Workspace.builder()
            .userId(userId)
            .name("test-workspace")
            .platform(MessagePlatformType.DISCORD)
            .externalId("ext_" + UUID.randomUUID().toString().substring(0, 8))
            .notificationChannelId("ch_test")
            .build();
    return workspaceRepository.save(ws);
  }

  protected Wallet createWallet(UUID workspaceId) {
    Wallet wallet =
        Wallet.builder()
            .workspaceId(workspaceId)
            .name("test-wallet")
            .walletAddress("0xabc")
            .build();
    return walletRepository.save(wallet);
  }

  protected Wallet createWallet(UUID workspaceId, String name, String address) {
    Wallet wallet =
        Wallet.builder().workspaceId(workspaceId).name(name).walletAddress(address).build();
    return walletRepository.save(wallet);
  }
}
