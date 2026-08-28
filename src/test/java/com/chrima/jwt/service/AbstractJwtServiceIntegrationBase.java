package com.chrima.jwt.service;

import com.chrima.jwt.config.JwtProperties;
import com.chrima.user.config.PasswordEncoderConfig;
import com.chrima.user.repository.UserRepository;
import com.chrima.user.service.UserService;
import org.junit.jupiter.api.AfterEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import({JwtService.class, UserService.class, JwtProperties.class, PasswordEncoderConfig.class})
public abstract class AbstractJwtServiceIntegrationBase {

  @Container
  static PostgreSQLContainer<?> postgres =
      new PostgreSQLContainer<>("postgres:16-alpine")
          .withDatabaseName("chrima")
          .withUsername("postgres")
          .withPassword("password");

  @DynamicPropertySource
  static void registerProperties(DynamicPropertyRegistry registry) {
    registry.add("spring.datasource.url", postgres::getJdbcUrl);
    registry.add("spring.datasource.username", postgres::getUsername);
    registry.add("spring.datasource.password", postgres::getPassword);
    registry.add("spring.datasource.driver-class-name", postgres::getDriverClassName);
  }

  @Autowired protected JwtService jwtService;

  @Autowired protected UserService userService;

  @Autowired protected UserRepository userRepository;

  @Autowired protected JwtProperties jwtProperties;

  @AfterEach
  void tearDown() {
    userRepository.deleteAll();
  }
}
