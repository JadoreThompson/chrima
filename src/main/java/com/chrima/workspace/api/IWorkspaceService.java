package com.chrima.workspace.api;

import com.chrima.workspace.dto.WorkspaceResponse;
import com.chrima.workspace.model.enums.MessagePlatformType;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

public interface IWorkspaceService {

  WorkspaceResponse create(
      UUID userId,
      String name,
      MessagePlatformType platform,
      String externalId,
      String notificationChannelId);

  WorkspaceResponse getById(UUID workspaceId);

  WorkspaceResponse get(UUID workspaceId, UUID userId);

  Page<WorkspaceResponse> getByUser(UUID userId, Pageable pageable);

  default Page<WorkspaceResponse> getByUser(UUID userId, int page, int limit) {
    return getByUser(userId, PageRequest.of(page - 1, limit));
  }

  WorkspaceResponse getByExternalId(String externalId);

  WorkspaceResponse update(
      UUID workspaceId, UUID userId, String name, String notificationChannelId);

  void delete(UUID workspaceId, UUID userId);
}
