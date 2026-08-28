package com.chrima.jwt.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.jwt.api.dto.JwtPayload;
import com.chrima.jwt.config.JwtProperties;
import com.chrima.user.service.UserService;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

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
    JwtPayload payload = svc.decode(token);
    assertThat(payload.getSub()).isEqualTo(sub);
    assertThat(payload.getEmail()).isEqualTo("user@test.com");
    assertThat(payload.getWorkspaceId()).isNull();
    assertThat(payload.getExp()).isNotNull();
  }

  @Test
  void shouldEncodeWithWorkspaceId() {
    JwtProperties props = new JwtProperties();
    JwtService svc = jwtServiceWithProps(props);
    UUID sub = UUID.randomUUID();
    UUID wsId = UUID.randomUUID();
    String token = svc.encode(sub, "ws@test.com", wsId);
    JwtPayload payload = svc.decode(token);
    assertThat(payload.getWorkspaceId()).isEqualTo(wsId);
  }

  @Test
  void shouldDecodeJwtMatchesDecode() {
    JwtProperties props = new JwtProperties();
    JwtService svc = jwtServiceWithProps(props);
    UUID sub = UUID.randomUUID();
    String token = svc.encode(sub, "match@test.com", null);
    assertThat(svc.decode(token).getSub()).isEqualTo(svc.decodeJwt(token).getSub());
    assertThat(svc.decode(token).getEmail()).isEqualTo(svc.decodeJwt(token).getEmail());
  }
}
