package com.chrima.user.controller;

import com.chrima.jwt.api.JwtPayload;
import com.chrima.jwt.config.security.JwtAuthenticationFilter;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.UserProfileBuilder;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.dto.UserProfile;
import com.chrima.workspace.api.IWorkspaceService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * User controller exposing user-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/user/router.py} which exposes {@code GET /users/me}.
 */
@Slf4j
@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
public class UserController {

  private final IUserService userService;
  private final IWorkspaceService workspaceService;

  /**
   * Returns the authenticated user's profile including workspace metas.
   *
   * <p>Authentication is provided by {@link JwtAuthenticationFilter} which validates the JWT cookie
   * (alias {@code chrima-cookie} by default) and populates the security context with a {@link
   * JwtPayload} principal — mirroring Python's {@code depends_jwt}. The controller then fetches the
   * user and their workspaces (page 1, limit 100).
   *
   * @param payload authenticated principal injected from the security context
   * @return user profile with workspaces
   */
  @GetMapping("/me")
  public ResponseEntity<UserProfile> me(@AuthenticationPrincipal JwtPayload payload) {
    log.debug("Fetching profile for user sub={}", payload.getSubject());
    UserDto userDto = userService.getById(payload.getSubject());
    UserProfile profile = UserProfileBuilder.build(userDto, workspaceService);
    return ResponseEntity.ok(profile);
  }
}
