package com.chrima.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.auth.api.dto.LoginRequest;
import com.chrima.auth.exception.InvalidLoginCredentialsException;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.exception.UserNotFoundException;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthServiceVerifyCredentialsTest {

  @Mock IUserService userService;
  @Mock PasswordEncoder passwordEncoder;

  @Test
  void shouldVerifyWithCorrectCredentials() {
    AuthService authService = new AuthService(userService, passwordEncoder);
    UUID id = UUID.randomUUID();
    UserDto stored =
        UserDto.builder()
            .id(id)
            .username("testuser")
            .email("test@example.com")
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();
    when(userService.findByEmail("test@example.com")).thenReturn(stored);
    when(userService.getPasswordHashByEmail("test@example.com"))
        .thenReturn("hashed_password_value");
    when(passwordEncoder.matches("correct_pw", "hashed_password_value")).thenReturn(true);

    LoginRequest req =
        LoginRequest.builder().email("test@example.com").password("correct_pw").build();
    UserDto result = authService.verifyCredentials(req);

    verify(userService).findByEmail("test@example.com");
    verify(passwordEncoder).matches("correct_pw", "hashed_password_value");
    assertThat(result.getId()).isEqualTo(id);
    assertThat(result.getEmail()).isEqualTo("test@example.com");
  }

  @Test
  void shouldThrowWhenUserNotFound() {
    AuthService authService = new AuthService(userService, passwordEncoder);
    when(userService.findByEmail("unknown@test.com")).thenThrow(new UserNotFoundException());

    LoginRequest req = LoginRequest.builder().email("unknown@test.com").password("pw").build();
    assertThatThrownBy(() -> authService.verifyCredentials(req))
        .isInstanceOf(InvalidLoginCredentialsException.class);
  }

  @Test
  void shouldThrowOnWrongPassword() {
    AuthService authService = new AuthService(userService, passwordEncoder);
    UserDto stored =
        UserDto.builder()
            .id(UUID.randomUUID())
            .username("testuser")
            .email("test@example.com")
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();
    when(userService.findByEmail("test@example.com")).thenReturn(stored);
    when(userService.getPasswordHashByEmail("test@example.com")).thenReturn("hash");
    when(passwordEncoder.matches("wrong_pw", "hash")).thenReturn(false);

    LoginRequest req =
        LoginRequest.builder().email("test@example.com").password("wrong_pw").build();
    assertThatThrownBy(() -> authService.verifyCredentials(req))
        .isInstanceOf(InvalidLoginCredentialsException.class);
    verify(passwordEncoder).matches("wrong_pw", "hash");
  }
}
