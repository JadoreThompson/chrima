package com.chrima.workspace.dto;

import com.chrima.workspace.api.enums.MessagePlatformType;
import com.chrima.workspace.model.Workspace;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class CreateWorkspaceRequest {
  String name;
  MessagePlatformType platform;
  String externalId;
  String notificationChannelId;

  public static CreateWorkspaceRequest from(Workspace workspace) {
    return CreateWorkspaceRequest.builder()
        .name(workspace.getName())
        .platform(workspace.getPlatform())
        .externalId(workspace.getExternalId())
        .notificationChannelId(workspace.getNotificationChannelId())
        .build();
  }
}
