package com.chrima.user.controller;

import com.chrima.auth.util.AuthUtil;
import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.dto.JwtPayload;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.dto.UserProfile;
import com.chrima.workspace.api.IWorkspaceService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
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
  private final IJwtService jwtService;

  /**
   * Returns the authenticated user's profile including workspace metas.
   *
   * <p>Validates the JWT cookie, fetches the user and their workspaces (page 1, limit 100), and
   * returns a {@link UserProfile}. Mirrors Python's {@code GET /users/me} which calls {@code
   * user_service.get_by_id} and {@code workspace_service.get_by_user(page=1, limit=100)}.
   *
   * @param token JWT cookie value (alias {@code chrima-cookie} by default)
   * @return user profile with workspaces
   */
  @GetMapping("/me")
  public ResponseEntity<UserProfile> me(
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload jwt = jwtService.validate(token);
    log.debug("Fetching profile for user sub={}", jwt.getSub());
    UserDto userDto = userService.getById(jwt.getSub());
    UserProfile profile = AuthUtil.buildUserProfile(userDto, workspaceService);
    return ResponseEntity.ok(profile);
  }
}
