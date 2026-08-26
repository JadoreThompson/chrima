package com.chrima.workspace.dto;

import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class UpdateWorkspaceRequest {
  String name;
  String notificationChannelId;
}
