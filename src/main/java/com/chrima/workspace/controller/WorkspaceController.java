package com.chrima.workspace.controller;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import com.chrima.workspace.api.IWorkspaceService;
import com.chrima.workspace.api.dto.WorkspaceResponse;
import com.chrima.workspace.dto.CreateWorkspaceRequest;
import com.chrima.workspace.dto.UpdateWorkspaceRequest;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Workspace controller exposing workspace-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/workspace/router.py}.
 */
@Slf4j
@RestController
@RequestMapping("/workspaces")
@RequiredArgsConstructor
public class WorkspaceController {

  private final IWorkspaceService workspaceService;
  private final IJwtService jwtService;

  @PostMapping
  public ResponseEntity<WorkspaceResponse> createWorkspace(
      @RequestBody CreateWorkspaceRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    WorkspaceResponse workspace =
        workspaceService.create(
            payload.getSubject(),
            body.getName(),
            body.getPlatform(),
            body.getExternalId(),
            body.getNotificationChannelId());
    return ResponseEntity.status(HttpStatus.CREATED).body(workspace);
  }

  @GetMapping("/{workspaceId}")
  public ResponseEntity<WorkspaceResponse> getWorkspace(
      @PathVariable UUID workspaceId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    return ResponseEntity.ok(workspaceService.get(workspaceId, payload.getSubject()));
  }

  @GetMapping
  public ResponseEntity<Page<WorkspaceResponse>> listWorkspaces(
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "10") int limit,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    return ResponseEntity.ok(workspaceService.getByUser(payload.getSubject(), page, limit));
  }

  @PatchMapping("/{workspaceId}")
  public ResponseEntity<WorkspaceResponse> updateWorkspace(
      @PathVariable UUID workspaceId,
      @RequestBody UpdateWorkspaceRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    WorkspaceResponse workspace =
        workspaceService.update(
            workspaceId, payload.getSubject(), body.getName(), body.getNotificationChannelId());
    return ResponseEntity.ok(workspace);
  }

  @DeleteMapping("/{workspaceId}")
  public ResponseEntity<Void> deleteWorkspace(
      @PathVariable UUID workspaceId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    workspaceService.delete(workspaceId, payload.getSubject());
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }
}
