package com.chrima.user.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.dto.JwtPayload;
import com.chrima.user.api.IUserService;
import com.chrima.user.api.dto.UserDto;
import com.chrima.user.exception.UserNotFoundException;
import com.chrima.workspace.api.IWorkspaceService;
import java.time.Instant;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(UserController.class)
class UserControllerMvcTest {

  @Autowired MockMvc mockMvc;

  @MockitoBean IJwtService jwtService;

  @MockitoBean IUserService userService;

  @MockitoBean IWorkspaceService workspaceService;

  @Test
  void shouldReturn404WhenUserNotFound() throws Exception {
    UUID userId = UUID.randomUUID();
    JwtPayload payload =
        JwtPayload.builder()
            .sub(userId)
            .email("ghost@test.com")
            .exp(Instant.now().plusSeconds(3600))
            .workspaceId(null)
            .build();
    when(jwtService.validate(any())).thenReturn(payload);
    when(userService.getById(userId)).thenThrow(new UserNotFoundException());

    mockMvc
        .perform(get("/users/me").cookie(new jakarta.servlet.http.Cookie("chrima-cookie", "dummy")))
        .andExpect(status().isNotFound());
  }

  @Test
  void shouldReturn401WhenJwtInvalid() throws Exception {
    when(jwtService.validate(any()))
        .thenThrow(new com.chrima.jwt.exception.JwtException("Invalid token"));

    mockMvc
        .perform(get("/users/me").cookie(new jakarta.servlet.http.Cookie("chrima-cookie", "bad")))
        .andExpect(status().isUnauthorized());
  }

  @Test
  void shouldReturn200WhenUserFound() throws Exception {
    UUID userId = UUID.randomUUID();
    JwtPayload payload =
        JwtPayload.builder()
            .sub(userId)
            .email("test@test.com")
            .exp(Instant.now().plusSeconds(3600))
            .workspaceId(null)
            .build();
    UserDto userDto =
        UserDto.builder()
            .id(userId)
            .username("testuser")
            .email("test@test.com")
            .createdAt(Instant.now())
            .updatedAt(Instant.now())
            .build();

    when(jwtService.validate(any())).thenReturn(payload);
    when(userService.getById(userId)).thenReturn(userDto);
    when(workspaceService.getByUser(userId, 1, 100))
        .thenReturn(new org.springframework.data.domain.PageImpl<>(java.util.List.of()));

    mockMvc
        .perform(get("/users/me").cookie(new jakarta.servlet.http.Cookie("chrima-cookie", "valid")))
        .andExpect(status().isOk());
  }
}
