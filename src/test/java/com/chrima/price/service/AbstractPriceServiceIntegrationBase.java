package com.chrima.price.service;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.chrima.events.api.IEventService;
import com.chrima.price.repository.PriceRepository;
import com.chrima.product.api.IProductService;
import com.chrima.product.api.dto.ProductResponse;
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
@Import({PriceService.class})
public abstract class AbstractPriceServiceIntegrationBase {

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

  @Autowired protected PriceService priceService;

  @Autowired protected PriceRepository priceRepository;

  @MockitoBean protected IWorkspaceService workspaceService;

  @MockitoBean protected IProductService productService;

  @MockitoBean protected IEventService eventService;

  @AfterEach
  void tearDown() {
    priceRepository.deleteAll();
  }

  protected UUID mockWorkspaceExists(UUID workspaceId) {
    when(workspaceService.getById(any()))
        .thenReturn(WorkspaceResponse.builder().id(workspaceId).build());
    return workspaceId;
  }

  protected UUID mockProductExists(UUID productId) {
    when(productService.getById(any())).thenReturn(ProductResponse.builder().id(productId).build());
    return productId;
  }
}
