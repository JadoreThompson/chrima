package com.chrima.user.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.chrima.auth.api.dto.RegisterRequest;
import com.chrima.jwt.config.JwtProperties;
import com.chrima.user.repository.UserRepository;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.repository.WorkspaceRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.Cookie;
import java.util.UUID;
import org.junit.jupiter.api.BeforeEach;
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
class UserControllerIntegrationTest {

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
  @Autowired UserRepository userRepository;
  @Autowired WorkspaceRepository workspaceRepository;
  @Autowired com.chrima.jwt.api.IJwtService jwtService;

  @BeforeEach
  void cleanUp() {
    workspaceRepository.deleteAll();
    userRepository.deleteAll();
  }

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
            .andReturn();
    return result.getResponse().getCookie(jwtProperties.getCookieAlias());
  }

  @Test
  void shouldReturnCurrentUserWhenAuthenticated() throws Exception {
    Cookie cookie = register("currentuser", "current@test.com", "secure_pass_123");

    mockMvc
        .perform(get("/users/me").cookie(cookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.username").value("currentuser"))
        .andExpect(jsonPath("$.email").value("current@test.com"))
        .andExpect(jsonPath("$.id").isNotEmpty())
        .andExpect(jsonPath("$.createdAt").isNotEmpty())
        .andExpect(jsonPath("$.updatedAt").isNotEmpty())
        .andExpect(jsonPath("$.workspaces").isArray());
  }

  @Test
  void shouldReturn401WithoutAuth() throws Exception {
    mockMvc.perform(get("/users/me")).andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturn401WithInvalidToken() throws Exception {
    Cookie invalidCookie = new Cookie(jwtProperties.getCookieAlias(), "invalid.token.value");
    mockMvc.perform(get("/users/me").cookie(invalidCookie)).andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturn401WithTokenForNonExistentUser() throws Exception {
    // create a token for a random user that does not exist in DB
    UUID randomUserId = UUID.randomUUID();
    String token = jwtService.encode(randomUserId, "ghost@test.com", null);
    Cookie cookie = new Cookie(jwtProperties.getCookieAlias(), token);

    mockMvc.perform(get("/users/me").cookie(cookie)).andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturnEmptyWorkspacesWhenNoneExist() throws Exception {
    Cookie cookie = register("noworkspace", "noworkspace@test.com", "secure_pass_123");

    mockMvc
        .perform(get("/users/me").cookie(cookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.workspaces").isArray())
        .andExpect(jsonPath("$.workspaces.length()").value(0));
  }

  @Test
  void shouldReturnWorkspacesWhenUserHasWorkspaces() throws Exception {
    Cookie cookie = register("wsuser", "ws@example.com", "secure_pass_123");

    // fetch current user id via /users/me to create workspaces for correct owner
    MvcResult meResult =
        mockMvc.perform(get("/users/me").cookie(cookie)).andExpect(status().isOk()).andReturn();
    String body = meResult.getResponse().getContentAsString();
    UUID userId = UUID.fromString(objectMapper.readTree(body).get("id").asText());

    // create workspace directly via repository (mirrors AnalyticsControllerIntegrationTest)
    Workspace ws =
        workspaceRepository.save(
            Workspace.builder()
                .userId(userId)
                .name("My Workspace")
                .platform(com.chrima.workspace.api.enums.MessagePlatformType.DISCORD)
                .externalId("guild_123")
                .notificationChannelId("ch_456")
                .build());

    mockMvc
        .perform(get("/users/me").cookie(cookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.workspaces.length()").value(1))
        .andExpect(jsonPath("$.workspaces[0].id").value(ws.getId().toString()))
        .andExpect(jsonPath("$.workspaces[0].name").value("My Workspace"));
  }

  @Test
  void shouldReturnMultipleWorkspaces() throws Exception {
    Cookie cookie = register("multiws", "multiws@test.com", "secure_pass_123");

    MvcResult meResult =
        mockMvc.perform(get("/users/me").cookie(cookie)).andExpect(status().isOk()).andReturn();
    UUID userId =
        UUID.fromString(
            objectMapper.readTree(meResult.getResponse().getContentAsString()).get("id").asText());

    Workspace ws1 =
        workspaceRepository.save(
            Workspace.builder()
                .userId(userId)
                .name("Workspace One")
                .platform(com.chrima.workspace.api.enums.MessagePlatformType.DISCORD)
                .externalId("ext-1-" + UUID.randomUUID())
                .notificationChannelId("ch-1")
                .build());
    Workspace ws2 =
        workspaceRepository.save(
            Workspace.builder()
                .userId(userId)
                .name("Workspace Two")
                .platform(com.chrima.workspace.api.enums.MessagePlatformType.DISCORD)
                .externalId("ext-2-" + UUID.randomUUID())
                .notificationChannelId("ch-2")
                .build());

    mockMvc
        .perform(get("/users/me").cookie(cookie))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.workspaces.length()").value(2))
        .andExpect(jsonPath("$.workspaces[?(@.name=='Workspace One')]").exists())
        .andExpect(jsonPath("$.workspaces[?(@.name=='Workspace Two')]").exists());
  }

  @Test
  void shouldNotLeakWorkspacesFromOtherUser() throws Exception {
    Cookie cookieUserA = register("userA", "userA@test.com", "pass");
    Cookie cookieUserB = register("userB", "userB@test.com", "pass");

    MvcResult meB =
        mockMvc
            .perform(get("/users/me").cookie(cookieUserB))
            .andExpect(status().isOk())
            .andReturn();
    UUID userBId =
        UUID.fromString(
            objectMapper.readTree(meB.getResponse().getContentAsString()).get("id").asText());

    workspaceRepository.save(
        Workspace.builder()
            .userId(userBId)
            .name("B Workspace")
            .platform(com.chrima.workspace.api.enums.MessagePlatformType.DISCORD)
            .externalId("ext-b-" + UUID.randomUUID())
            .notificationChannelId("ch-b")
            .build());

    // userA should see no workspaces even though userB has one
    mockMvc
        .perform(get("/users/me").cookie(cookieUserA))
        .andExpect(status().isOk())
        .andExpect(jsonPath("$.workspaces.length()").value(0));
  }
}
