package com.chrima.wallet.repository;

import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;
import com.chrima.user.repository.UserRepository;
import com.chrima.wallet.model.Wallet;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.model.enums.MessagePlatformType;
import com.chrima.workspace.repository.WorkspaceRepository;
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

  @Autowired protected WorkspaceRepository workspaceRepository;

  @Autowired protected UserRepository userRepository;

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
    try {
      workspaceRepository.deleteAll();
    } catch (Exception ignored) {
    }
    try {
      userRepository.deleteAll();
    } catch (Exception ignored) {
    }
  }

  protected User createUser(String username, String email) {
    User user =
        User.builder().username(username).email(email).password("hashed").tier(Tier.FREE).build();
    return userRepository.save(user);
  }

  protected User createUser() {
    return createUser(
        "user-" + UUID.randomUUID().toString().substring(0, 8), UUID.randomUUID() + "@example.com");
  }

  protected Workspace createWorkspace(UUID userId, String externalId) {
    Workspace ws =
        Workspace.builder()
            .userId(userId)
            .name("ws-" + externalId)
            .platform(MessagePlatformType.DISCORD)
            .externalId(externalId)
            .notificationChannelId("ch_" + externalId)
            .build();
    return workspaceRepository.save(ws);
  }

  protected Workspace createWorkspace(UUID userId) {
    return createWorkspace(userId, "ext_" + UUID.randomUUID().toString().substring(0, 8));
  }

  protected Wallet createWallet(UUID workspaceId, String name, String address) {
    Wallet wallet =
        Wallet.builder().workspaceId(workspaceId).name(name).walletAddress(address).build();
    return walletRepository.save(wallet);
  }

  protected Wallet createWalletWithWorkspace() {
    User user = createUser();
    Workspace ws = createWorkspace(user.getId());
    return createWallet(ws.getId(), "wallet", "0xabc");
  }
}
