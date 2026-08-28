package com.chrima.auth.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.cookie;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.chrima.auth.api.dto.ChangeEmailRequest;
import com.chrima.auth.api.dto.ChangePasswordRequest;
import com.chrima.auth.api.dto.ChangeUsernameRequest;
import com.chrima.auth.api.dto.LoginRequest;
import com.chrima.auth.api.dto.RegisterRequest;
import com.chrima.auth.api.dto.SelectWorkspaceRequest;
import com.chrima.jwt.config.JwtProperties;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.Cookie;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@SpringBootTest
@AutoConfigureMockMvc
@Testcontainers
class AuthControllerIntegrationTest {

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

  @Autowired MockMvc mockMvc;
  @Autowired ObjectMapper objectMapper;
  @Autowired JwtProperties jwtProperties;

  private Cookie register(String username, String email, String password) throws Exception {
    RegisterRequest req =
        RegisterRequest.builder().username(username).email(email).password(password).build();
    MvcResult result =
        mockMvc
            .perform(
                post("/auth/register")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(req)))
            .andExpect(status().isNoContent())
            .andExpect(cookie().exists(jwtProperties.getCookieAlias()))
            .andReturn();
    return result.getResponse().getCookie(jwtProperties.getCookieAlias());
  }

  private Cookie login(String email, String password) throws Exception {
    LoginRequest req = LoginRequest.builder().email(email).password(password).build();
    MvcResult result =
        mockMvc
            .perform(
                post("/auth/login")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(req)))
            .andExpect(status().isNoContent())
            .andExpect(cookie().exists(jwtProperties.getCookieAlias()))
            .andReturn();
    return result.getResponse().getCookie(jwtProperties.getCookieAlias());
  }

  @Test
  void shouldRegisterSuccess() throws Exception {
    register("newuser", "new@test.com", "secure_pass_123");
  }

  @Test
  void shouldReturn422OnMissingEmail() throws Exception {
    RegisterRequest req = RegisterRequest.builder().username("u").password("p").build();
    mockMvc
        .perform(
            post("/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isUnprocessableEntity());
  }

  @Test
  void shouldLoginSuccess() throws Exception {
    register("loginuser", "login@test.com", "test_pass_123");
    login("login@test.com", "test_pass_123");
  }

  @Test
  void shouldReturn401OnWrongPassword() throws Exception {
    register("loginuser2", "login2@test.com", "test_pass_123");
    LoginRequest req =
        LoginRequest.builder().email("login2@test.com").password("wrong_password").build();
    mockMvc
        .perform(
            post("/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturn401OnNonexistentUser() throws Exception {
    LoginRequest req = LoginRequest.builder().email("nobody@test.com").password("any").build();
    mockMvc
        .perform(
            post("/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturn404OnNonexistentWorkspace() throws Exception {
    Cookie cookie = register("ws404user", "ws404@test.com", "pass");
    SelectWorkspaceRequest req =
        SelectWorkspaceRequest.builder().workspaceId(UUID.randomUUID()).build();
    mockMvc
        .perform(
            post("/auth/select-workspace")
                .cookie(cookie)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isNotFound());
  }

  @Test
  void shouldReturn422OnMissingWorkspaceId() throws Exception {
    Cookie cookie = register("wsmissing", "wsmissing@test.com", "pass");
    mockMvc
        .perform(
            post("/auth/select-workspace")
                .cookie(cookie)
                .contentType(MediaType.APPLICATION_JSON)
                .content("{}"))
        .andExpect(status().isUnprocessableEntity());
  }

  @Test
  void shouldReturn401WithoutJwtForSelectWorkspace() throws Exception {
    SelectWorkspaceRequest req =
        SelectWorkspaceRequest.builder().workspaceId(UUID.randomUUID()).build();
    mockMvc
        .perform(
            post("/auth/select-workspace")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldLogoutSuccess() throws Exception {
    Cookie cookie = register("logoutuser", "logout@test.com", "pass");
    mockMvc
        .perform(post("/auth/logout").cookie(cookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.message").value("Logged out"));
  }

  @Test
  void shouldReturn401WithoutJwtForLogout() throws Exception {
    mockMvc.perform(post("/auth/logout")).andExpect(status().isUnauthorized());
  }

  @Test
  void shouldChangeUsernameSuccess() throws Exception {
    Cookie cookie = register("changeuser", "change@test.com", "test_pass_123");
    ChangeUsernameRequest req = ChangeUsernameRequest.builder().username("newname").build();
    MvcResult result =
        mockMvc
            .perform(
                post("/auth/change-username")
                    .cookie(cookie)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(req)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.username").value("newname"))
            .andReturn();
    assertThat(result.getResponse().getCookie(jwtProperties.getCookieAlias())).isNotNull();
  }

  @Test
  void shouldReturn401WithoutAuthForChangeUsername() throws Exception {
    ChangeUsernameRequest req = ChangeUsernameRequest.builder().username("any").build();
    mockMvc
        .perform(
            post("/auth/change-username")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldChangePasswordSuccess() throws Exception {
    Cookie cookie = register("pwuser", "pw@test.com", "old_pass_123");
    ChangePasswordRequest req =
        ChangePasswordRequest.builder()
            .oldPassword("old_pass_123")
            .newPassword("new_pass_456")
            .build();
    mockMvc
        .perform(
            post("/auth/change-password")
                .cookie(cookie)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.username").value("pwuser"));

    // verify new password works for login
    LoginRequest loginReq =
        LoginRequest.builder().email("pw@test.com").password("new_pass_456").build();
    mockMvc
        .perform(
            post("/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(loginReq)))
        .andExpect(status().isNoContent());
  }

  @Test
  void shouldReturn401OnWrongOldPassword() throws Exception {
    Cookie cookie = register("pwuser2", "pw2@test.com", "old_pass_123");
    ChangePasswordRequest req =
        ChangePasswordRequest.builder()
            .oldPassword("wrong_pass")
            .newPassword("new_pass_456")
            .build();
    mockMvc
        .perform(
            post("/auth/change-password")
                .cookie(cookie)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldChangeEmailSuccess() throws Exception {
    Cookie cookie = register("emailuser", "email@test.com", "pass");
    ChangeEmailRequest req = ChangeEmailRequest.builder().email("newemail@test.com").build();
    mockMvc
        .perform(
            post("/auth/change-email")
                .cookie(cookie)
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.email").value("newemail@test.com"));
  }

  @Test
  void shouldReturn401WithoutAuthForChangeEmail() throws Exception {
    ChangeEmailRequest req = ChangeEmailRequest.builder().email("any@test.com").build();
    mockMvc
        .perform(
            post("/auth/change-email")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(req)))
        .andExpect(status().isUnauthorized());
  }
}
