package com.chrima.workspace.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.workspace.api.enums.MessagePlatformType;
import com.chrima.workspace.model.Workspace;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.data.domain.PageRequest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@DataJpaTest
@Testcontainers
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class WorkspaceRepositoryTest {

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

  @Autowired private WorkspaceRepository workspaceRepository;

  @AfterEach
  void tearDown() {
    try {
      workspaceRepository.deleteAll();
    } catch (Exception ignored) {
      // transaction may be aborted after constraint violation test
    }
  }

  private Workspace createWorkspace(UUID userId, String name, String externalId) {
    Workspace ws =
        Workspace.builder()
            .userId(userId)
            .name(name)
            .platform(MessagePlatformType.DISCORD)
            .externalId(externalId)
            .notificationChannelId("ch_" + externalId)
            .build();
    return workspaceRepository.save(ws);
  }

  @Test
  void shouldSaveAndFindById() {
    UUID userId = UUID.randomUUID();
    Workspace saved = createWorkspace(userId, "test-workspace", "ext_001");

    Optional<Workspace> found = workspaceRepository.findById(saved.getId());

    assertThat(found).isPresent();
    assertThat(found.get().getId()).isEqualTo(saved.getId());
    assertThat(found.get().getName()).isEqualTo("test-workspace");
    assertThat(found.get().getPlatform()).isEqualTo(MessagePlatformType.DISCORD);
    assertThat(found.get().getExternalId()).isEqualTo("ext_001");
    assertThat(found.get().getNotificationChannelId()).isEqualTo("ch_ext_001");
    assertThat(found.get().getUserId()).isEqualTo(userId);
  }

  @Test
  void findByExternalIdShouldReturnWorkspaceWhenExists() {
    UUID userId = UUID.randomUUID();
    Workspace saved = createWorkspace(userId, "ws", "ext_find");

    Optional<Workspace> found = workspaceRepository.findByExternalId("ext_find");

    assertThat(found).isPresent();
    assertThat(found.get().getId()).isEqualTo(saved.getId());
  }

  @Test
  void findByExternalIdShouldReturnEmptyWhenNotFound() {
    UUID userId = UUID.randomUUID();
    createWorkspace(userId, "ws", "ext_exists");

    Optional<Workspace> found = workspaceRepository.findByExternalId("nonexistent");

    assertThat(found).isEmpty();
  }

  @Test
  void findByIdAndUserIdShouldReturnWhenMatches() {
    UUID userId = UUID.randomUUID();
    Workspace saved = createWorkspace(userId, "ws", "ext_1");

    Optional<Workspace> found = workspaceRepository.findByIdAndUserId(saved.getId(), userId);

    assertThat(found).isPresent();
    assertThat(found.get().getId()).isEqualTo(saved.getId());
  }

  @Test
  void findByIdAndUserIdShouldReturnEmptyWhenWrongUser() {
    UUID userId = UUID.randomUUID();
    Workspace saved = createWorkspace(userId, "ws", "ext_1");

    Optional<Workspace> found =
        workspaceRepository.findByIdAndUserId(saved.getId(), UUID.randomUUID());

    assertThat(found).isEmpty();
  }

  @Test
  void findByIdAndUserIdShouldReturnEmptyWhenNotFound() {
    UUID userId = UUID.randomUUID();
    createWorkspace(userId, "ws", "ext_1");

    Optional<Workspace> found = workspaceRepository.findByIdAndUserId(UUID.randomUUID(), userId);

    assertThat(found).isEmpty();
  }

  @Test
  void findByUserIdShouldReturnAllForUser() {
    UUID userId = UUID.randomUUID();
    createWorkspace(userId, "ws-a", "ext_a");
    createWorkspace(userId, "ws-b", "ext_b");

    List<Workspace> found = workspaceRepository.findByUserId(userId);

    assertThat(found).hasSize(2);
  }

  @Test
  void findByUserIdShouldReturnEmptyWhenNoWorkspaces() {
    UUID userId = UUID.randomUUID();
    createWorkspace(userId, "ws", "ext_1");

    List<Workspace> found = workspaceRepository.findByUserId(UUID.randomUUID());

    assertThat(found).isEmpty();
  }

  @Test
  void findByUserIdWithPageableShouldPaginate() {
    UUID userId = UUID.randomUUID();
    for (int i = 0; i < 3; i++) {
      createWorkspace(userId, "ws-" + i, "ext_" + i);
    }

    var page1 = workspaceRepository.findByUserId(userId, PageRequest.of(0, 2));
    var page2 = workspaceRepository.findByUserId(userId, PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.hasNext()).isFalse();
    assertThat(page1.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldPersistTimestamps() {
    UUID userId = UUID.randomUUID();
    Workspace saved = createWorkspace(userId, "ws", "ext_ts");
    workspaceRepository.flush();

    assertThat(saved.getId()).isNotNull();
    assertThat(saved.getCreatedAt()).isNotNull();
    assertThat(saved.getUpdatedAt()).isNotNull();

    Workspace fetched = workspaceRepository.findById(saved.getId()).orElseThrow();
    assertThat(fetched.getCreatedAt()).isNotNull();
    assertThat(fetched.getUpdatedAt()).isNotNull();
  }

  @Test
  void shouldUpdateNameAndChannelId() {
    UUID userId = UUID.randomUUID();
    Workspace saved = createWorkspace(userId, "original", "ext_upd");

    saved.setName("updated");
    saved.setNotificationChannelId("new_ch");
    workspaceRepository.save(saved);
    workspaceRepository.flush();

    Workspace fetched = workspaceRepository.findById(saved.getId()).orElseThrow();
    assertThat(fetched.getName()).isEqualTo("updated");
    assertThat(fetched.getNotificationChannelId()).isEqualTo("new_ch");
  }

  @Test
  void shouldPersistUserId() {
    UUID userId = UUID.randomUUID();
    Workspace ws =
        Workspace.builder()
            .userId(userId)
            .name("user-id-test")
            .platform(MessagePlatformType.DISCORD)
            .externalId("ext_uid")
            .notificationChannelId("ch_uid")
            .build();

    Workspace saved = workspaceRepository.saveAndFlush(ws);

    assertThat(saved.getUserId()).isEqualTo(userId);
    Workspace fetched = workspaceRepository.findById(saved.getId()).orElseThrow();
    assertThat(fetched.getUserId()).isEqualTo(userId);
  }

  @Test
  void shouldDeleteWorkspace() {
    UUID userId = UUID.randomUUID();
    Workspace saved = createWorkspace(userId, "to-delete", "ext_del");

    workspaceRepository.delete(saved);
    workspaceRepository.flush();

    assertThat(workspaceRepository.findById(saved.getId())).isEmpty();
  }

  @Test
  void findByIdShouldReturnEmptyForUnknownId() {
    Optional<Workspace> found = workspaceRepository.findById(UUID.randomUUID());
    assertThat(found).isEmpty();
  }
}
