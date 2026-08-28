package com.chrima.jwt.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.jwt.config.JwtProperties;
import com.chrima.user.service.UserService;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.security.oauth2.jwt.Jwt;

@ExtendWith(MockitoExtension.class)
class JwtServiceEncodeTest {

  @Mock UserService userService;

  private JwtService jwtServiceWithProps(JwtProperties props) {
    return new JwtService(props, userService);
  }

  @Test
  void shouldEncodeAndDecodeRoundtrip() {
    JwtProperties props = new JwtProperties();
    JwtService svc = jwtServiceWithProps(props);
    UUID sub = UUID.randomUUID();
    String token = svc.encode(sub, "user@test.com", null);
    Jwt jwt = svc.decode(token);
    assertThat(jwt.getSubject()).isEqualTo(sub.toString());
    assertThat(jwt.getClaimAsString("em")).isEqualTo("user@test.com");
    assertThat(jwt.getClaimAsString("workspace_id")).isNull();
    assertThat(jwt.getExpiresAt()).isNotNull();
  }

  @Test
  void shouldEncodeWithWorkspaceId() {
    JwtProperties props = new JwtProperties();
    JwtService svc = jwtServiceWithProps(props);
    UUID sub = UUID.randomUUID();
    UUID wsId = UUID.randomUUID();
    String token = svc.encode(sub, "ws@test.com", wsId);
    Jwt jwt = svc.decode(token);
    assertThat(jwt.getClaimAsString("workspace_id")).isEqualTo(wsId.toString());
  }

  @Test
  void shouldDecodeJwtMatchesDecode() {
    JwtProperties props = new JwtProperties();
    JwtService svc = jwtServiceWithProps(props);
    UUID sub = UUID.randomUUID();
    String token = svc.encode(sub, "match@test.com", null);
    assertThat(svc.decode(token).getSubject()).isEqualTo(svc.decodeJwt(token).getSubject());
    assertThat(svc.decode(token).getClaimAsString("em"))
        .isEqualTo(svc.decodeJwt(token).getClaimAsString("em"));
  }
}
