package com.chrima.user.dto;

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
}
