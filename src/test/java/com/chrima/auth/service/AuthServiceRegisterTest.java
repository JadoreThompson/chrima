package com.chrima.auth.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.chrima.auth.api.dto.RegisterRequest;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.crypto.password.PasswordEncoder;

@ExtendWith(MockitoExtension.class)
class AuthServiceRegisterTest {

  @Mock IUserService userService;
  @Mock PasswordEncoder passwordEncoder;

  @Test
  void shouldRegisterUserSuccessfully() {
    AuthService authService = new AuthService(userService, passwordEncoder);
    RegisterRequest req =
        RegisterRequest.builder()
            .username("testuser")
            .email("test@example.com")
            .password("plain_pw")
            .build();
    UserDto created =
        UserDto.builder()
            .id(UUID.randomUUID())
            .username("testuser")
            .email("test@example.com")
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();
    when(passwordEncoder.encode("plain_pw")).thenReturn("hashed_password");
    when(userService.create("testuser", "test@example.com", "hashed_password")).thenReturn(created);

    UserDto result = authService.register(req);

    verify(passwordEncoder).encode("plain_pw");
    verify(userService).create("testuser", "test@example.com", "hashed_password");
    assertThat(result.getId()).isEqualTo(created.getId());
  }

  @Test
  void shouldHashPasswordBeforeCreatingUser() {
    AuthService authService = new AuthService(userService, passwordEncoder);
    RegisterRequest req =
        RegisterRequest.builder().username("u").email("u@t.com").password("raw").build();
    UserDto created =
        UserDto.builder()
            .id(UUID.randomUUID())
            .username("u")
            .email("u@t.com")
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();
    when(passwordEncoder.encode("raw")).thenReturn("hashed_pw");
    when(userService.create(any(), any(), any())).thenReturn(created);

    authService.register(req);

    verify(passwordEncoder).encode("raw");
    verify(userService).create("u", "u@t.com", "hashed_pw");
  }
}
