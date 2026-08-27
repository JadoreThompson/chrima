package com.chrima.wallet.service;

import com.chrima.user.config.PasswordEncoderConfig;
import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;
import com.chrima.user.repository.UserRepository;
import com.chrima.user.service.UserService;
import com.chrima.wallet.repository.WalletRepository;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.model.enums.MessagePlatformType;
import com.chrima.workspace.repository.WorkspaceRepository;
import com.chrima.workspace.service.WorkspaceService;

import java.util.UUID;

import org.junit.jupiter.api.AfterEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;

@DataJpaTest
@Import({
        WalletService.class,
        WorkspaceService.class,
        UserService.class,
        PasswordEncoderConfig.class
})
public abstract class AbstractWalletServiceIntegrationBase {

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

    @Autowired
    protected WalletService walletService;

    @Autowired
    protected WalletRepository walletRepository;

    @Autowired
    protected WorkspaceRepository workspaceRepository;

    @Autowired
    protected UserRepository userRepository;

    @AfterEach
    void tearDown() {
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
}
