package com.chrima.workspace.api.dto;

import com.chrima.workspace.api.enums.MessagePlatformType;
import com.chrima.workspace.model.Workspace;
import java.time.Instant;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class WorkspaceResponse {
  UUID id;
  MessagePlatformType platform;
  String externalId;
  String notificationChannelId;
  String name;
  Instant createdAt;
  Instant updatedAt;

  public static WorkspaceResponse from(Workspace workspace) {
    return WorkspaceResponse.builder()
        .id(workspace.getId())
        .platform(workspace.getPlatform())
        .externalId(workspace.getExternalId())
        .notificationChannelId(workspace.getNotificationChannelId())
        .name(workspace.getName())
        .createdAt(workspace.getCreatedAt())
        .updatedAt(workspace.getUpdatedAt())
        .build();
  }
}
