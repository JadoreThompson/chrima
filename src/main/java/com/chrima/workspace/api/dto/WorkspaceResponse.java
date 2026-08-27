package com.chrima.workspace.api.dto;

import com.chrima.workspace.api.enums.MessagePlatformType;
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
}
