package com.chrima.auth.util;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.dto.UserProfile;
import com.chrima.user.api.dto.WorkspaceMeta;
import com.chrima.workspace.api.IWorkspaceService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;

@ExtendWith(MockitoExtension.class)
class AuthUtilTest {

  @Mock IWorkspaceService workspaceService;

  private UserDto sampleUserDto() {
    return UserDto.builder()
        .id(UUID.randomUUID())
        .username("testuser")
        .email("test@example.com")
        .createdAt(Instant.parse("2024-01-01T12:00:00Z"))
        .updatedAt(Instant.parse("2024-06-01T12:00:00Z"))
        .build();
  }

  @Test
  void shouldBuildProfileWithWorkspaces() {
    UserDto user = sampleUserDto();
    UUID wsId1 = UUID.randomUUID();
    UUID wsId2 = UUID.randomUUID();
    WorkspaceResponse ws1 = WorkspaceResponse.builder().id(wsId1).name("Workspace One").build();
    WorkspaceResponse ws2 = WorkspaceResponse.builder().id(wsId2).name("Workspace Two").build();
    Page<WorkspaceResponse> page = new PageImpl<>(List.of(ws1, ws2), PageRequest.of(0, 100), 2);
    when(workspaceService.getByUser(eq(user.getId()), eq(1), eq(100))).thenReturn(page);

    UserProfile result = AuthUtil.buildUserProfile(user, workspaceService);

    assertThat(result).isNotNull();
    assertThat(result.getId()).isEqualTo(user.getId());
    assertThat(result.getUsername()).isEqualTo(user.getUsername());
    assertThat(result.getEmail()).isEqualTo(user.getEmail());
    assertThat(result.getCreatedAt()).isEqualTo(user.getCreatedAt());
    assertThat(result.getUpdatedAt()).isEqualTo(user.getUpdatedAt());
    assertThat(result.getWorkspaces()).hasSize(2);
    assertThat(result.getWorkspaces())
        .containsExactly(
            WorkspaceMeta.builder().id(wsId1).name("Workspace One").build(),
            WorkspaceMeta.builder().id(wsId2).name("Workspace Two").build());
  }

  @Test
  void shouldBuildProfileWithEmptyWorkspaces() {
    UserDto user = sampleUserDto();
    Page<WorkspaceResponse> page = new PageImpl<>(List.of(), PageRequest.of(0, 100), 0);
    when(workspaceService.getByUser(any(), eq(1), eq(100))).thenReturn(page);

    UserProfile result = AuthUtil.buildUserProfile(user, workspaceService);

    assertThat(result.getWorkspaces()).isEmpty();
  }

  @Test
  void shouldBubbleUpWorkspaceServiceError() {
    UserDto user = sampleUserDto();
    when(workspaceService.getByUser(any(), eq(1), eq(100)))
        .thenThrow(new RuntimeException("db down"));

    assertThatThrownBy(() -> AuthUtil.buildUserProfile(user, workspaceService))
        .isInstanceOf(RuntimeException.class)
        .hasMessageContaining("db down");
  }
}
