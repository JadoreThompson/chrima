package com.chrima.workspace.dto;

import com.chrima.workspace.api.enums.MessagePlatformType;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class CreateWorkspaceRequest {
  String name;
  MessagePlatformType platform;
  String externalId;
  String notificationChannelId;
}
