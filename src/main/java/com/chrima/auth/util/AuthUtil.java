package com.chrima.auth.util;

import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.dto.UserProfile;
import com.chrima.user.api.dto.WorkspaceMeta;
import com.chrima.workspace.api.IWorkspaceService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
import java.util.List;
import org.springframework.data.domain.Page;

/** Utility to build {@link UserProfile} from a {@link UserDto} by fetching workspaces. */
public final class AuthUtil {

  private AuthUtil() {}

  /**
   * Convert a {@link UserDto} into a {@link UserProfile} by fetching the user's workspaces.
   *
   * @param userDto user dto
   * @param workspaceService workspace service
   * @return user profile containing workspace metas
   */
  public static UserProfile buildUserProfile(UserDto userDto, IWorkspaceService workspaceService) {
    Page<WorkspaceResponse> page = workspaceService.getByUser(userDto.getId(), 1, 100);
    List<WorkspaceMeta> workspaces =
        page.getContent().stream()
            .map(ws -> WorkspaceMeta.builder().id(ws.getId()).name(ws.getName()).build())
            .toList();
    return UserProfile.builder()
        .id(userDto.getId())
        .username(userDto.getUsername())
        .email(userDto.getEmail())
        .createdAt(userDto.getCreatedAt())
        .updatedAt(userDto.getUpdatedAt())
        .workspaces(workspaces)
        .build();
  }
}
