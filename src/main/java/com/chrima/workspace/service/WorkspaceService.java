package com.chrima.workspace.service;

import com.chrima.user.api.IUserService;
import com.chrima.workspace.api.IWorkspaceService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
import com.chrima.workspace.api.enums.MessagePlatformType;
import com.chrima.workspace.exception.WorkspaceNotFoundException;
import com.chrima.workspace.model.Workspace;
import com.chrima.workspace.repository.WorkspaceRepository;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class WorkspaceService implements IWorkspaceService {

  private final WorkspaceRepository workspaceRepository;
  private final IUserService userService;

  @Override
  @Transactional
  public WorkspaceResponse create(
      UUID userId,
      String name,
      MessagePlatformType platform,
      String externalId,
      String notificationChannelId) {
    log.info("Creating workspace userId={} externalId={}", userId, externalId);
    userService.ensureExists(userId);
    Workspace workspace =
        Workspace.builder()
            .userId(userId)
            .name(name)
            .platform(platform)
            .externalId(externalId)
            .notificationChannelId(notificationChannelId)
            .build();
    Workspace saved = workspaceRepository.saveAndFlush(workspace);
    log.info("Workspace created id={} userId={}", saved.getId(), userId);
    return WorkspaceResponse.from(saved);
  }

  @Override
  @Transactional(readOnly = true)
  public WorkspaceResponse getById(UUID workspaceId) {
    Workspace workspace =
        workspaceRepository
            .findById(workspaceId)
            .orElseThrow(
                () -> {
                  log.warn("Workspace not found id={}", workspaceId);
                  return new WorkspaceNotFoundException(workspaceId);
                });
    return WorkspaceResponse.from(workspace);
  }

  @Override
  @Transactional(readOnly = true)
  public WorkspaceResponse get(UUID workspaceId, UUID userId) {
    Workspace workspace = getWorkspaceOrThrow(workspaceId, userId);
    return WorkspaceResponse.from(workspace);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<WorkspaceResponse> getByUser(UUID userId, Pageable pageable) {
    return workspaceRepository.findByUserId(userId, pageable).map(WorkspaceResponse::from);
  }

  @Override
  @Transactional(readOnly = true)
  public WorkspaceResponse getByExternalId(String externalId) {
    Workspace workspace =
        workspaceRepository
            .findByExternalId(externalId)
            .orElseThrow(
                () -> {
                  log.warn("Workspace not found externalId={}", externalId);
                  return new WorkspaceNotFoundException(externalId);
                });
    return WorkspaceResponse.from(workspace);
  }

  @Override
  @Transactional
  public WorkspaceResponse update(
      UUID workspaceId, UUID userId, String name, String notificationChannelId) {
    if (name == null && notificationChannelId == null) {
      throw new IllegalArgumentException("At least one field must be provided.");
    }
    Workspace workspace = getWorkspaceOrThrow(workspaceId, userId);
    if (name != null) {
      workspace.setName(name);
    }
    if (notificationChannelId != null) {
      workspace.setNotificationChannelId(notificationChannelId);
    }
    Workspace saved = workspaceRepository.save(workspace);
    log.info("Workspace updated id={} userId={}", workspaceId, userId);
    return WorkspaceResponse.from(saved);
  }

  @Override
  @Transactional
  public void delete(UUID workspaceId, UUID userId) {
    Workspace workspace = getWorkspaceOrThrow(workspaceId, userId);
    workspaceRepository.delete(workspace);
    log.info("Workspace deleted id={} userId={}", workspaceId, userId);
  }

  private Workspace getWorkspaceOrThrow(UUID workspaceId, UUID userId) {
    return workspaceRepository
        .findByIdAndUserId(workspaceId, userId)
        .orElseThrow(
            () -> {
              log.warn("Workspace not found id={} userId={}", workspaceId, userId);
              return new WorkspaceNotFoundException(workspaceId);
            });
  }
}
