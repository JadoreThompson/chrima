package com.chrima.user.api.dto;

import com.chrima.user.model.User;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class UserProfile {
  UUID id;
  String username;
  String email;
  Instant createdAt;
  Instant updatedAt;
  List<WorkspaceMeta> workspaces;

  public static UserProfile from(User user, List<WorkspaceMeta> workspaces) {
    return UserProfile.builder()
        .id(user.getId())
        .username(user.getUsername())
        .email(user.getEmail())
        .createdAt(user.getCreatedAt())
        .updatedAt(user.getUpdatedAt())
        .workspaces(workspaces)
        .build();
  }
}
