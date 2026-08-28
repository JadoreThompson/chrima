package com.chrima.auth.controller;

import com.chrima.auth.api.IAuthService;
import com.chrima.auth.api.dto.ChangeEmailRequest;
import com.chrima.auth.api.dto.ChangePasswordRequest;
import com.chrima.auth.api.dto.ChangeUsernameRequest;
import com.chrima.auth.api.dto.LoginRequest;
import com.chrima.auth.api.dto.RegisterRequest;
import com.chrima.auth.api.dto.SelectWorkspaceRequest;
import com.chrima.discord.api.IDiscordService;
import com.chrima.discord.api.dto.DiscordUserResponse;
import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.UserProfileBuilder;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.dto.UserProfile;
import com.chrima.workspace.api.IWorkspaceService;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

  private final IAuthService authService;
  private final IJwtService jwtService;
  private final IUserService userService;
  private final IWorkspaceService workspaceService;
  private final IDiscordService discordService;

  @PostMapping("/register")
  public ResponseEntity<Void> register(
      @Valid @RequestBody RegisterRequest body, HttpServletResponse response) {
    UserDto user = authService.register(body);
    String token = jwtService.setCookie(response, user.getId(), user.getEmail(), null);
    userService.setJwtToken(user.getId(), token);
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }

  @PostMapping("/login")
  public ResponseEntity<Void> login(
      @Valid @RequestBody LoginRequest body, HttpServletResponse response) {
    UserDto user = authService.verifyCredentials(body);
    String token = jwtService.setCookie(response, user.getId(), user.getEmail(), null);
    userService.setJwtToken(user.getId(), token);
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }

  @PostMapping("/select-workspace")
  public ResponseEntity<Void> selectWorkspace(
      @Valid @RequestBody SelectWorkspaceRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload payload = jwtService.validate(token);
    UUID sub = payload.getSubject();
    String email = payload.getEmail();
    workspaceService.getById(body.getWorkspaceId());
    String newToken = jwtService.setCookie(response, sub, email, body.getWorkspaceId());
    userService.setJwtToken(sub, newToken);
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }

  @PostMapping("/logout")
  public ResponseEntity<java.util.Map<String, String>> logout(
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload payload = jwtService.validate(token);
    UUID sub = payload.getSubject();
    jwtService.removeCookie(response);
    userService.setJwtToken(sub, null);
    return ResponseEntity.ok(java.util.Map.of("message", "Logged out"));
  }

  @PostMapping("/change-username")
  public ResponseEntity<UserProfile> changeUsername(
      @Valid @RequestBody ChangeUsernameRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload payload = jwtService.validate(token);
    UUID sub = payload.getSubject();
    UserDto userDto = userService.changeUsername(sub, body.getUsername());
    UserProfile profile = UserProfileBuilder.build(userDto, workspaceService);
    String newToken =
        jwtService.setCookie(
            response, userDto.getId(), userDto.getEmail(), payload.getWorkspaceId());
    userService.setJwtToken(userDto.getId(), newToken);
    return ResponseEntity.ok(profile);
  }

  @PostMapping("/change-password")
  public ResponseEntity<UserProfile> changePassword(
      @Valid @RequestBody ChangePasswordRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload payload = jwtService.validate(token);
    UUID sub = payload.getSubject();
    UserDto userDto = userService.changePassword(sub, body.getOldPassword(), body.getNewPassword());
    UserProfile profile = UserProfileBuilder.build(userDto, workspaceService);
    String newToken =
        jwtService.setCookie(
            response, userDto.getId(), userDto.getEmail(), payload.getWorkspaceId());
    userService.setJwtToken(userDto.getId(), newToken);
    return ResponseEntity.ok(profile);
  }

  @PostMapping("/change-email")
  public ResponseEntity<UserProfile> changeEmail(
      @Valid @RequestBody ChangeEmailRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload payload = jwtService.validate(token);
    UUID sub = payload.getSubject();
    UserDto userDto = userService.changeEmail(sub, body.getEmail());
    UserProfile profile = UserProfileBuilder.build(userDto, workspaceService);
    String newToken =
        jwtService.setCookie(
            response, userDto.getId(), userDto.getEmail(), payload.getWorkspaceId());
    userService.setJwtToken(userDto.getId(), newToken);
    return ResponseEntity.ok(profile);
  }

  /**
   * Discord OAuth callback for authenticated Chrima users (workspace owners).
   *
   * <p>Mirrors {@code GET /auth/discord/oauth/callback} in {@code
   * chrima-backend/src/chrima/auth/router.py}. Exchanges the Discord authorization code for an
   * access token and stores the OAuth payload under the user.
   *
   * @param code Discord authorization code
   * @param token JWT cookie
   * @return 204 No Content
   */
  @GetMapping("/discord/oauth/callback")
  public ResponseEntity<Void> discordOauthCallback(
      @RequestParam String code,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    JwtPayload payload = jwtService.validate(token);
    UUID sub = payload.getSubject();
    discordService.handleCallback(sub, code);
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }

  /**
   * Public Discord subscriber callback used by the checkout page to identify a customer.
   *
   * <p>Mirrors {@code GET /auth/discord/subscriber-callback} in {@code
   * chrima-backend/src/chrima/auth/router.py}. Exchanges the Discord authorization code and stores
   * the customer's OAuth payload under their Discord user id (no Chrima account required).
   *
   * @param code Discord authorization code
   * @return the Discord user profile
   */
  @GetMapping("/discord/subscriber-callback")
  public ResponseEntity<DiscordUserResponse> discordSubscriberCallback(@RequestParam String code) {
    return ResponseEntity.ok(discordService.handleSubscriberCallback(code));
  }
}
