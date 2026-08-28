package com.chrima.jwt.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.jwt.api.JwtPayload;
import com.chrima.jwt.exception.JwtException;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class JwtServiceValidateTest extends AbstractJwtServiceIntegrationBase {

  @Test
  void shouldValidateTokenWithRealUser() {
    var user = userService.create("validateuser", "validate@test.com", "h");
    String token = jwtService.encode(user.getId(), user.getEmail(), null);
    userService.setJwtToken(user.getId(), token);

    JwtPayload payload = jwtService.validate(token);
    assertThat(payload.getSubject()).isEqualTo(user.getId());
    assertThat(payload.getEmail()).isEqualTo(user.getEmail());
  }

  @Test
  void shouldRejectWrongToken() {
    var user = userService.create("validateuser2", "validate2@test.com", "h");
    String correct = jwtService.encode(user.getId(), user.getEmail(), null);
    userService.setJwtToken(user.getId(), correct);
    String wrong = jwtService.encode(user.getId(), user.getEmail(), null);

    assertThatThrownBy(() -> jwtService.validate(wrong))
        .isInstanceOf(JwtException.class)
        .hasMessageContaining("Invalid jwt token");
  }

  @Test
  void shouldRejectNonexistentUser() {
    String token = jwtService.encode(UUID.randomUUID(), "ghost@test.com", null);
    assertThatThrownBy(() -> jwtService.validate(token))
        .isInstanceOf(JwtException.class)
        .hasMessageContaining("Invalid jwt token");
  }
}
