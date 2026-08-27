package com.chrima.product.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.chrima.product.repository.ProductRepository;
import com.chrima.wallet.api.IWalletService;
import com.chrima.wallet.api.dto.WalletResponse;
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
@Import({ProductService.class})
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

  @MockitoBean protected IWorkspaceService workspaceService;

  @MockitoBean protected IWalletService walletService;

  @AfterEach
  void tearDown() {
    productRepository.deleteAll();
  }

  protected UUID mockWorkspaceExists(UUID workspaceId) {
    when(workspaceService.getById(any()))
        .thenReturn(WorkspaceResponse.builder().id(workspaceId).build());
    return workspaceId;
  }

  protected UUID mockWalletExists(UUID walletId) {
    when(walletService.getById(any())).thenReturn(WalletResponse.builder().id(walletId).build());
    return walletId;
  }
}
