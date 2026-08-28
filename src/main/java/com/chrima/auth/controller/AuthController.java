package com.chrima.auth.controller;

import com.chrima.auth.api.IAuthService;
import com.chrima.auth.api.dto.ChangeEmailRequest;
import com.chrima.auth.api.dto.ChangePasswordRequest;
import com.chrima.auth.api.dto.ChangeUsernameRequest;
import com.chrima.auth.api.dto.LoginRequest;
import com.chrima.auth.api.dto.RegisterRequest;
import com.chrima.auth.api.dto.SelectWorkspaceRequest;
import com.chrima.auth.util.AuthUtil;
import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.dto.JwtPayload;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.api.dto.UserProfile;
import com.chrima.workspace.api.IWorkspaceService;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
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
    JwtPayload jwt = jwtService.validate(token);
    // ensure workspace exists
    workspaceService.getById(body.getWorkspaceId());
    String newToken =
        jwtService.setCookie(response, jwt.getSub(), jwt.getEmail(), body.getWorkspaceId());
    userService.setJwtToken(jwt.getSub(), newToken);
    return ResponseEntity.status(HttpStatus.NO_CONTENT).build();
  }

  @PostMapping("/logout")
  public ResponseEntity<java.util.Map<String, String>> logout(
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload jwt = jwtService.validate(token);
    jwtService.removeCookie(response);
    userService.setJwtToken(jwt.getSub(), null);
    return ResponseEntity.ok(java.util.Map.of("message", "Logged out"));
  }

  @PostMapping("/change-username")
  public ResponseEntity<UserProfile> changeUsername(
      @Valid @RequestBody ChangeUsernameRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload jwt = jwtService.validate(token);
    UserDto userDto = userService.changeUsername(jwt.getSub(), body.getUsername());
    UserProfile profile = AuthUtil.buildUserProfile(userDto, workspaceService);
    String newToken =
        jwtService.setCookie(response, userDto.getId(), userDto.getEmail(), jwt.getWorkspaceId());
    userService.setJwtToken(userDto.getId(), newToken);
    return ResponseEntity.ok(profile);
  }

  @PostMapping("/change-password")
  public ResponseEntity<UserProfile> changePassword(
      @Valid @RequestBody ChangePasswordRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload jwt = jwtService.validate(token);
    UserDto userDto =
        userService.changePassword(jwt.getSub(), body.getOldPassword(), body.getNewPassword());
    UserProfile profile = AuthUtil.buildUserProfile(userDto, workspaceService);
    String newToken =
        jwtService.setCookie(response, userDto.getId(), userDto.getEmail(), jwt.getWorkspaceId());
    userService.setJwtToken(userDto.getId(), newToken);
    return ResponseEntity.ok(profile);
  }

  @PostMapping("/change-email")
  public ResponseEntity<UserProfile> changeEmail(
      @Valid @RequestBody ChangeEmailRequest body,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token,
      HttpServletResponse response) {
    JwtPayload jwt = jwtService.validate(token);
    UserDto userDto = userService.changeEmail(jwt.getSub(), body.getEmail());
    UserProfile profile = AuthUtil.buildUserProfile(userDto, workspaceService);
    String newToken =
        jwtService.setCookie(response, userDto.getId(), userDto.getEmail(), jwt.getWorkspaceId());
    userService.setJwtToken(userDto.getId(), newToken);
    return ResponseEntity.ok(profile);
  }
}
