package com.chrima.workspace.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.user.config.PasswordEncoderConfig;
import com.chrima.user.exception.UserNotFoundException;
import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;
import com.chrima.user.repository.UserRepository;
import com.chrima.user.service.UserService;
import com.chrima.workspace.dto.PaginatedWorkspaceResponse;
import com.chrima.workspace.dto.WorkspaceResponse;
import com.chrima.workspace.exception.WorkspaceNotFoundException;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.model.enums.MessagePlatformType;
import com.chrima.workspace.repository.WorkspaceRepository;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
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
@Import({WorkspaceService.class, UserService.class, PasswordEncoderConfig.class})
class WorkspaceServiceIntegrationTest {

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

  @Autowired private WorkspaceService workspaceService;

  @Autowired private WorkspaceRepository workspaceRepository;

  @Autowired private UserRepository userRepository;

  @AfterEach
  void tearDown() {
    try {
      workspaceRepository.deleteAll();
    } catch (Exception ignored) {
    }
    try {
      userRepository.deleteAll();
    } catch (Exception ignored) {
    }
  }

  private User createUser() {
    User user =
        User.builder()
            .username("user-" + UUID.randomUUID().toString().substring(0, 8))
            .email(UUID.randomUUID() + "@example.com")
            .password("hashed")
            .tier(Tier.FREE)
            .build();
    return userRepository.save(user);
  }

  // ---- create ----

  @Test
  void shouldCreateWorkspaceAndPersist() {
    User user = createUser();

    WorkspaceResponse ws =
        workspaceService.create(
            user.getId(), "test-workspace", MessagePlatformType.DISCORD, "ext_123", "ch_1");

    assertThat(ws.getId()).isNotNull();
    assertThat(ws.getName()).isEqualTo("test-workspace");
    assertThat(ws.getPlatform()).isEqualTo(MessagePlatformType.DISCORD);
    assertThat(ws.getExternalId()).isEqualTo("ext_123");
    assertThat(ws.getNotificationChannelId()).isEqualTo("ch_1");
    assertThat(ws.getCreatedAt()).isNotNull();
    assertThat(ws.getUpdatedAt()).isNotNull();

    Workspace row = workspaceRepository.findById(ws.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("test-workspace");
  }

  @Test
  void shouldThrowWhenUserNotFoundOnCreate() {
    UUID randomUserId = UUID.randomUUID();

    assertThatThrownBy(
            () ->
                workspaceService.create(
                    randomUserId, "test", MessagePlatformType.DISCORD, "ext", "ch"))
        .isInstanceOf(UserNotFoundException.class);
  }

  // ---- getById ----

  @Test
  void shouldGetById() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(
            user.getId(), "get-by-id", MessagePlatformType.DISCORD, "ext", "ch");

    WorkspaceResponse fetched = workspaceService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getName()).isEqualTo("get-by-id");
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    assertThatThrownBy(() -> workspaceService.getById(UUID.randomUUID()))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  // ---- get ----

  @Test
  void shouldGet() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(user.getId(), "get-ws", MessagePlatformType.DISCORD, "ext", "ch");

    WorkspaceResponse fetched = workspaceService.get(created.getId(), user.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldThrowWhenGetNotFound() {
    User user = createUser();

    assertThatThrownBy(() -> workspaceService.get(UUID.randomUUID(), user.getId()))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenGetWrongUser() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(
            user.getId(), "wrong-user", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.get(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WorkspaceNotFoundException.class);

    // row still exists
    assertThat(workspaceRepository.findById(created.getId())).isPresent();
  }

  // ---- getByExternalId ----

  @Test
  void shouldGetByExternalId() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(
            user.getId(), "ext-test", MessagePlatformType.DISCORD, "ext_uniq", "ch");

    WorkspaceResponse fetched = workspaceService.getByExternalId("ext_uniq");

    assertThat(fetched.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldThrowWhenGetByExternalIdNotFound() {
    assertThatThrownBy(() -> workspaceService.getByExternalId("nonexistent"))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  // ---- getByUser ----

  @Test
  void shouldGetByUserReturnsWorkspaces() {
    User user = createUser();
    WorkspaceResponse w1 =
        workspaceService.create(user.getId(), "ws-a", MessagePlatformType.DISCORD, "ext_a", "ch_a");
    WorkspaceResponse w2 =
        workspaceService.create(user.getId(), "ws-b", MessagePlatformType.DISCORD, "ext_b", "ch_b");

    PaginatedWorkspaceResponse result = workspaceService.getByUser(user.getId(), 1, 10);

    assertThat(result.getSize()).isEqualTo(2);
    assertThat(result.getData())
        .extracting(WorkspaceResponse::getId)
        .containsExactlyInAnyOrder(w1.getId(), w2.getId());
    assertThat(result.isHasNext()).isFalse();
    assertThat(result.getPage()).isEqualTo(1);
  }

  @Test
  void shouldPaginate() {
    User user = createUser();
    for (int i = 0; i < 3; i++) {
      workspaceService.create(
          user.getId(), "ws", MessagePlatformType.DISCORD, "ext_" + i, "ch_" + i);
    }

    PaginatedWorkspaceResponse result = workspaceService.getByUser(user.getId(), 1, 2);

    assertThat(result.getSize()).isEqualTo(2);
    assertThat(result.isHasNext()).isTrue();
  }

  @Test
  void shouldReturnEmptyWhenNoWorkspaces() {
    PaginatedWorkspaceResponse result = workspaceService.getByUser(UUID.randomUUID(), 1, 10);

    assertThat(result.getSize()).isEqualTo(0);
    assertThat(result.getData()).isEmpty();
    assertThat(result.isHasNext()).isFalse();
  }

  @Test
  void shouldPaginateSecondPage() {
    User user = createUser();
    for (int i = 0; i < 3; i++) {
      workspaceService.create(
          user.getId(), "ws", MessagePlatformType.DISCORD, "ext_p" + i, "ch_p" + i);
    }

    PaginatedWorkspaceResponse page1 = workspaceService.getByUser(user.getId(), 1, 2);
    PaginatedWorkspaceResponse page2 = workspaceService.getByUser(user.getId(), 2, 2);

    assertThat(page1.getSize()).isEqualTo(2);
    assertThat(page1.isHasNext()).isTrue();
    assertThat(page2.getSize()).isEqualTo(1);
    assertThat(page2.isHasNext()).isFalse();
  }

  // ---- update ----

  @Test
  void shouldUpdateName() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(user.getId(), "original", MessagePlatformType.DISCORD, "ext", "ch");

    WorkspaceResponse updated =
        workspaceService.update(created.getId(), user.getId(), "updated-name", null);

    assertThat(updated.getName()).isEqualTo("updated-name");
    Workspace row = workspaceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("updated-name");
  }

  @Test
  void shouldUpdateChannelId() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(
            user.getId(), "ch-test", MessagePlatformType.DISCORD, "ext", "old_ch");

    WorkspaceResponse updated =
        workspaceService.update(created.getId(), user.getId(), null, "new_ch");

    assertThat(updated.getNotificationChannelId()).isEqualTo("new_ch");
    Workspace row = workspaceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getNotificationChannelId()).isEqualTo("new_ch");
  }

  @Test
  void shouldUpdateBothFields() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(user.getId(), "orig", MessagePlatformType.DISCORD, "ext", "old_ch");

    WorkspaceResponse updated =
        workspaceService.update(created.getId(), user.getId(), "new-name", "new_ch");

    assertThat(updated.getName()).isEqualTo("new-name");
    assertThat(updated.getNotificationChannelId()).isEqualTo("new_ch");
  }

  @Test
  void shouldThrowWhenUpdateWithNoFields() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(user.getId(), "test", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.update(created.getId(), user.getId(), null, null))
        .isInstanceOf(IllegalArgumentException.class);
  }

  @Test
  void shouldThrowWhenUpdateNotFound() {
    User user = createUser();

    assertThatThrownBy(() -> workspaceService.update(UUID.randomUUID(), user.getId(), "x", null))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenUpdateWrongUser() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(
            user.getId(), "wrong-user-upd", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.update(created.getId(), UUID.randomUUID(), "x", null))
        .isInstanceOf(WorkspaceNotFoundException.class);

    Workspace row = workspaceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("wrong-user-upd");
  }

  // ---- delete ----

  @Test
  void shouldDeleteWorkspaceAndVerifyGone() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(
            user.getId(), "to-delete", MessagePlatformType.DISCORD, "ext", "ch");

    workspaceService.delete(created.getId(), user.getId());

    assertThat(workspaceRepository.findById(created.getId())).isEmpty();
    assertThatThrownBy(() -> workspaceService.getById(created.getId()))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteNotFound() {
    User user = createUser();

    assertThatThrownBy(() -> workspaceService.delete(UUID.randomUUID(), user.getId()))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteWrongUser() {
    User user = createUser();
    WorkspaceResponse created =
        workspaceService.create(
            user.getId(), "wrong-user-del", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.delete(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WorkspaceNotFoundException.class);

    assertThat(workspaceRepository.findById(created.getId())).isPresent();
  }
}
