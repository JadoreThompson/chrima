package com.chrima.user.api.dto;

import com.chrima.user.model.User;
import java.time.Instant;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class UserDto {
  UUID id;
  String username;
  String email;
  Instant createdAt;
  Instant updatedAt;

  public static UserDto from(User user) {
    return UserDto.builder()
        .id(user.getId())
        .username(user.getUsername())
        .email(user.getEmail())
        .createdAt(user.getCreatedAt())
        .updatedAt(user.getUpdatedAt())
        .build();
  }
}
