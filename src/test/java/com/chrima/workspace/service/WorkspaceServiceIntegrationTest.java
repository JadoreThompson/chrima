package com.chrima.workspace.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;

import com.chrima.user.api.IUserService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
import com.chrima.workspace.api.enums.MessagePlatformType;
import com.chrima.workspace.exception.WorkspaceNotFoundException;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.repository.WorkspaceRepository;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.context.annotation.Import;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Import({WorkspaceService.class})
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

  @MockitoBean private IUserService userService;

  @AfterEach
  void tearDown() {
    try {
      workspaceRepository.deleteAll();
    } catch (Exception ignored) {
    }
  }

  // ---- create ----

  @Test
  void shouldCreateWorkspaceAndPersist() {
    UUID userId = UUID.randomUUID();

    WorkspaceResponse ws =
        workspaceService.create(
            userId, "test-workspace", MessagePlatformType.DISCORD, "ext_123", "ch_1");

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
    doThrow(new RuntimeException("User not found")).when(userService).ensureExists(any());

    assertThatThrownBy(
            () ->
                workspaceService.create(
                    randomUserId, "test", MessagePlatformType.DISCORD, "ext", "ch"))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("User not found");
  }

  // ---- getById ----

  @Test
  void shouldGetById() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "get-by-id", MessagePlatformType.DISCORD, "ext", "ch");

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
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "get-ws", MessagePlatformType.DISCORD, "ext", "ch");

    WorkspaceResponse fetched = workspaceService.get(created.getId(), userId);

    assertThat(fetched.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldThrowWhenGetNotFound() {
    UUID userId = UUID.randomUUID();

    assertThatThrownBy(() -> workspaceService.get(UUID.randomUUID(), userId))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenGetWrongUser() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "wrong-user", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.get(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WorkspaceNotFoundException.class);

    // row still exists
    assertThat(workspaceRepository.findById(created.getId())).isPresent();
  }

  // ---- getByExternalId ----

  @Test
  void shouldGetByExternalId() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "ext-test", MessagePlatformType.DISCORD, "ext_uniq", "ch");

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
    UUID userId = UUID.randomUUID();
    WorkspaceResponse w1 =
        workspaceService.create(userId, "ws-a", MessagePlatformType.DISCORD, "ext_a", "ch_a");
    WorkspaceResponse w2 =
        workspaceService.create(userId, "ws-b", MessagePlatformType.DISCORD, "ext_b", "ch_b");

    Page<WorkspaceResponse> result = workspaceService.getByUser(userId, PageRequest.of(0, 10));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.getContent())
        .extracting(WorkspaceResponse::getId)
        .containsExactlyInAnyOrder(w1.getId(), w2.getId());
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getNumber()).isEqualTo(0);
    assertThat(result.getTotalElements()).isEqualTo(2);
  }

  @Test
  void shouldPaginate() {
    UUID userId = UUID.randomUUID();
    for (int i = 0; i < 3; i++) {
      workspaceService.create(userId, "ws", MessagePlatformType.DISCORD, "ext_" + i, "ch_" + i);
    }

    Page<WorkspaceResponse> result = workspaceService.getByUser(userId, PageRequest.of(0, 2));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.hasNext()).isTrue();
    assertThat(result.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldReturnEmptyWhenNoWorkspaces() {
    Page<WorkspaceResponse> result =
        workspaceService.getByUser(UUID.randomUUID(), PageRequest.of(0, 10));

    assertThat(result.getContent()).isEmpty();
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getTotalElements()).isEqualTo(0);
  }

  @Test
  void shouldPaginateSecondPage() {
    UUID userId = UUID.randomUUID();
    for (int i = 0; i < 3; i++) {
      workspaceService.create(userId, "ws", MessagePlatformType.DISCORD, "ext_p" + i, "ch_p" + i);
    }

    Page<WorkspaceResponse> page1 = workspaceService.getByUser(userId, PageRequest.of(0, 2));
    Page<WorkspaceResponse> page2 = workspaceService.getByUser(userId, PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  @Test
  void shouldSupportLegacyPageAndLimitOverload() {
    UUID userId = UUID.randomUUID();
    for (int i = 0; i < 3; i++) {
      workspaceService.create(userId, "ws-l", MessagePlatformType.DISCORD, "ext_l" + i, "ch_l" + i);
    }

    Page<WorkspaceResponse> page1 = workspaceService.getByUser(userId, 1, 2);
    Page<WorkspaceResponse> page2 = workspaceService.getByUser(userId, 2, 2);

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  // ---- update ----

  @Test
  void shouldUpdateName() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "original", MessagePlatformType.DISCORD, "ext", "ch");

    WorkspaceResponse updated =
        workspaceService.update(created.getId(), userId, "updated-name", null);

    assertThat(updated.getName()).isEqualTo("updated-name");
    Workspace row = workspaceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("updated-name");
  }

  @Test
  void shouldUpdateChannelId() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "ch-test", MessagePlatformType.DISCORD, "ext", "old_ch");

    WorkspaceResponse updated = workspaceService.update(created.getId(), userId, null, "new_ch");

    assertThat(updated.getNotificationChannelId()).isEqualTo("new_ch");
    Workspace row = workspaceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getNotificationChannelId()).isEqualTo("new_ch");
  }

  @Test
  void shouldUpdateBothFields() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "orig", MessagePlatformType.DISCORD, "ext", "old_ch");

    WorkspaceResponse updated =
        workspaceService.update(created.getId(), userId, "new-name", "new_ch");

    assertThat(updated.getName()).isEqualTo("new-name");
    assertThat(updated.getNotificationChannelId()).isEqualTo("new_ch");
  }

  @Test
  void shouldThrowWhenUpdateWithNoFields() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "test", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.update(created.getId(), userId, null, null))
        .isInstanceOf(IllegalArgumentException.class);
  }

  @Test
  void shouldThrowWhenUpdateNotFound() {
    UUID userId = UUID.randomUUID();

    assertThatThrownBy(() -> workspaceService.update(UUID.randomUUID(), userId, "x", null))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenUpdateWrongUser() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "wrong-user-upd", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.update(created.getId(), UUID.randomUUID(), "x", null))
        .isInstanceOf(WorkspaceNotFoundException.class);

    Workspace row = workspaceRepository.findById(created.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("wrong-user-upd");
  }

  // ---- delete ----

  @Test
  void shouldDeleteWorkspaceAndVerifyGone() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "to-delete", MessagePlatformType.DISCORD, "ext", "ch");

    workspaceService.delete(created.getId(), userId);

    assertThat(workspaceRepository.findById(created.getId())).isEmpty();
    assertThatThrownBy(() -> workspaceService.getById(created.getId()))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteNotFound() {
    UUID userId = UUID.randomUUID();

    assertThatThrownBy(() -> workspaceService.delete(UUID.randomUUID(), userId))
        .isInstanceOf(WorkspaceNotFoundException.class);
  }

  @Test
  void shouldThrowWhenDeleteWrongUser() {
    UUID userId = UUID.randomUUID();
    WorkspaceResponse created =
        workspaceService.create(userId, "wrong-user-del", MessagePlatformType.DISCORD, "ext", "ch");

    assertThatThrownBy(() -> workspaceService.delete(created.getId(), UUID.randomUUID()))
        .isInstanceOf(WorkspaceNotFoundException.class);

    assertThat(workspaceRepository.findById(created.getId())).isPresent();
  }
}
