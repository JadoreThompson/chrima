package com.chrima.workspace.dto;

import com.chrima.workspace.model.Workspace;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class UpdateWorkspaceRequest {
  String name;
  String notificationChannelId;

  public static UpdateWorkspaceRequest from(Workspace workspace) {
    return UpdateWorkspaceRequest.builder()
        .name(workspace.getName())
        .notificationChannelId(workspace.getNotificationChannelId())
        .build();
  }
}
