package com.chrima.workspace.api;

import com.chrima.workspace.dto.PaginatedWorkspaceResponse;
import com.chrima.workspace.dto.WorkspaceResponse;
import com.chrima.workspace.model.enums.MessagePlatformType;
import java.util.UUID;

public interface IWorkspaceService {

  WorkspaceResponse create(
      UUID userId,
      String name,
      MessagePlatformType platform,
      String externalId,
      String notificationChannelId);

  WorkspaceResponse getById(UUID workspaceId);

  WorkspaceResponse get(UUID workspaceId, UUID userId);

  PaginatedWorkspaceResponse getByUser(UUID userId, int page, int limit);

  WorkspaceResponse getByExternalId(String externalId);

  WorkspaceResponse update(
      UUID workspaceId, UUID userId, String name, String notificationChannelId);

  void delete(UUID workspaceId, UUID userId);
}
