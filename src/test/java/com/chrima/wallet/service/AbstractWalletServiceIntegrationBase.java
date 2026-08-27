package com.chrima.wallet.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.chrima.wallet.repository.WalletRepository;
import com.chrima.workspace.api.IWorkspaceService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
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
@Import({WalletService.class})
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

  @Autowired protected WalletService walletService;

  @Autowired protected WalletRepository walletRepository;

  @MockitoBean protected IWorkspaceService workspaceService;

  @AfterEach
  void tearDown() {
    walletRepository.deleteAll();
  }

  protected UUID mockWorkspaceExists(UUID workspaceId) {
    when(workspaceService.getById(any()))
        .thenReturn(WorkspaceResponse.builder().id(workspaceId).build());
    return workspaceId;
  }
}
