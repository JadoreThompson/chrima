package com.chrima.user.api.dto;

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
}
