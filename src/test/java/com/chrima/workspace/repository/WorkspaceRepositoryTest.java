package com.chrima.workspace.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.user.model.User;
import com.chrima.user.model.enums.Tier;
import com.chrima.user.repository.UserRepository;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.model.enums.MessagePlatformType;
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

  @Autowired private UserRepository userRepository;

  @AfterEach
  void tearDown() {
    try {
      workspaceRepository.deleteAll();
    } catch (Exception ignored) {
      // transaction may be aborted after constraint violation test
    }
    try {
      userRepository.deleteAll();
    } catch (Exception ignored) {
      // transaction may be aborted after constraint violation test
    }
  }

  private User createUser(String username, String email) {
    User user =
        User.builder().username(username).email(email).password("hashed").tier(Tier.FREE).build();
    return userRepository.save(user);
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
    User user = createUser("alice", "alice@example.com");
    Workspace saved = createWorkspace(user.getId(), "test-workspace", "ext_001");

    Optional<Workspace> found = workspaceRepository.findById(saved.getId());

    assertThat(found).isPresent();
    assertThat(found.get().getId()).isEqualTo(saved.getId());
    assertThat(found.get().getName()).isEqualTo("test-workspace");
    assertThat(found.get().getPlatform()).isEqualTo(MessagePlatformType.DISCORD);
    assertThat(found.get().getExternalId()).isEqualTo("ext_001");
    assertThat(found.get().getNotificationChannelId()).isEqualTo("ch_ext_001");
    assertThat(found.get().getUserId()).isEqualTo(user.getId());
  }

  @Test
  void findByExternalIdShouldReturnWorkspaceWhenExists() {
    User user = createUser("bob", "bob@example.com");
    Workspace saved = createWorkspace(user.getId(), "ws", "ext_find");

    Optional<Workspace> found = workspaceRepository.findByExternalId("ext_find");

    assertThat(found).isPresent();
    assertThat(found.get().getId()).isEqualTo(saved.getId());
  }

  @Test
  void findByExternalIdShouldReturnEmptyWhenNotFound() {
    User user = createUser("carol", "carol@example.com");
    createWorkspace(user.getId(), "ws", "ext_exists");

    Optional<Workspace> found = workspaceRepository.findByExternalId("nonexistent");

    assertThat(found).isEmpty();
  }

  @Test
  void findByIdAndUserIdShouldReturnWhenMatches() {
    User user = createUser("dave", "dave@example.com");
    Workspace saved = createWorkspace(user.getId(), "ws", "ext_1");

    Optional<Workspace> found = workspaceRepository.findByIdAndUserId(saved.getId(), user.getId());

    assertThat(found).isPresent();
    assertThat(found.get().getId()).isEqualTo(saved.getId());
  }

  @Test
  void findByIdAndUserIdShouldReturnEmptyWhenWrongUser() {
    User user = createUser("eve", "eve@example.com");
    Workspace saved = createWorkspace(user.getId(), "ws", "ext_1");

    Optional<Workspace> found =
        workspaceRepository.findByIdAndUserId(saved.getId(), UUID.randomUUID());

    assertThat(found).isEmpty();
  }

  @Test
  void findByIdAndUserIdShouldReturnEmptyWhenNotFound() {
    User user = createUser("frank", "frank@example.com");
    createWorkspace(user.getId(), "ws", "ext_1");

    Optional<Workspace> found =
        workspaceRepository.findByIdAndUserId(UUID.randomUUID(), user.getId());

    assertThat(found).isEmpty();
  }

  @Test
  void findByUserIdShouldReturnAllForUser() {
    User user = createUser("grace", "grace@example.com");
    createWorkspace(user.getId(), "ws-a", "ext_a");
    createWorkspace(user.getId(), "ws-b", "ext_b");

    List<Workspace> found = workspaceRepository.findByUserId(user.getId());

    assertThat(found).hasSize(2);
  }

  @Test
  void findByUserIdShouldReturnEmptyWhenNoWorkspaces() {
    User user = createUser("henry", "henry@example.com");
    createWorkspace(user.getId(), "ws", "ext_1");

    List<Workspace> found = workspaceRepository.findByUserId(UUID.randomUUID());

    assertThat(found).isEmpty();
  }

  @Test
  void findByUserIdWithPageableShouldPaginate() {
    User user = createUser("iris", "iris@example.com");
    for (int i = 0; i < 3; i++) {
      createWorkspace(user.getId(), "ws-" + i, "ext_" + i);
    }

    var page1 = workspaceRepository.findByUserId(user.getId(), PageRequest.of(0, 2));
    var page2 = workspaceRepository.findByUserId(user.getId(), PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.hasNext()).isFalse();
    assertThat(page1.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldPersistTimestamps() {
    User user = createUser("tiertest", "tier@example.com");
    Workspace saved = createWorkspace(user.getId(), "ws", "ext_ts");
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
    User user = createUser("updateTest", "upd@example.com");
    Workspace saved = createWorkspace(user.getId(), "original", "ext_upd");

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
    User user = createUser("deltest", "del@example.com");
    Workspace saved = createWorkspace(user.getId(), "to-delete", "ext_del");

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
