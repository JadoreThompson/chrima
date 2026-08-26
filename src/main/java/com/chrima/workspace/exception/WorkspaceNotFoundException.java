package com.chrima.workspace.exception;

import java.util.UUID;

public class WorkspaceNotFoundException extends RuntimeException {

  private final UUID workspaceId;

  public WorkspaceNotFoundException(UUID workspaceId) {
    super("Workspace not found");
    this.workspaceId = workspaceId;
  }

  public WorkspaceNotFoundException(String externalId) {
    super("Workspace not found");
    this.workspaceId = null;
  }

  public UUID getWorkspaceId() {
    return workspaceId;
  }
}
