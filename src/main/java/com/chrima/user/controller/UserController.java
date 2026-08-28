package com.chrima.user.controller;

import com.chrima.auth.util.AuthUtil;
import com.chrima.jwt.config.security.JwtAuthenticationFilter;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.dto.UserProfile;
import com.chrima.workspace.api.IWorkspaceService;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
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
   * (alias {@code chrima-cookie} by default) and populates the security context with a native
   * Spring {@link Jwt} principal — mirroring Python's {@code depends_jwt}. The controller then
   * fetches the user and their workspaces (page 1, limit 100).
   *
   * @param jwt authenticated principal injected from the security context (Spring native JWT)
   * @return user profile with workspaces
   */
  @GetMapping("/me")
  public ResponseEntity<UserProfile> me(@AuthenticationPrincipal Jwt jwt) {
    UUID sub = UUID.fromString(jwt.getSubject());
    log.debug("Fetching profile for user sub={}", sub);
    UserDto userDto = userService.getById(sub);
    UserProfile profile = AuthUtil.buildUserProfile(userDto, workspaceService);
    return ResponseEntity.ok(profile);
  }
}
