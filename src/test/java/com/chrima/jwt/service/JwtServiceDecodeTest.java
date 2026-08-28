package com.chrima.jwt.service;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.jwt.config.JwtProperties;
import com.chrima.jwt.exception.JwtException;
import com.chrima.user.service.UserService;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class JwtServiceDecodeTest {

  @Mock UserService userService;

  private JwtService jwtServiceWithProps(JwtProperties props) {
    return new JwtService(props, userService);
  }

  @Test
  void shouldThrowOnExpiredToken() throws InterruptedException {
    JwtProperties shortProps = new JwtProperties();
    shortProps.setExpirySecs(0L);
    JwtService shortSvc = jwtServiceWithProps(shortProps);
    String token = shortSvc.encode(UUID.randomUUID(), "x@y.com", null);
    // ensure time moves past expiry (1s sleep, or tight loop)
    Thread.sleep(1100);
    JwtProperties normalProps = new JwtProperties();
    JwtService normalSvc = jwtServiceWithProps(normalProps);
    assertThatThrownBy(() -> normalSvc.decode(token))
        .isInstanceOf(JwtException.class)
        .hasMessageContaining("Token has expired");
  }

  @Test
  void shouldThrowOnInvalidSignature() {
    JwtProperties propsA = new JwtProperties();
    JwtProperties propsB = new JwtProperties();
    propsB.setSecret("different-secret-01234567890123456789-xyz");
    JwtService svcA = jwtServiceWithProps(propsA);
    JwtService svcB = jwtServiceWithProps(propsB);
    String token = svcB.encode(UUID.randomUUID(), "x@y.com", null);
    assertThatThrownBy(() -> svcA.decode(token))
        .isInstanceOf(JwtException.class)
        .hasMessageContaining("Invalid token");
  }

  @Test
  void shouldThrowOnGarbageToken() {
    JwtProperties props = new JwtProperties();
    JwtService svc = jwtServiceWithProps(props);
    assertThatThrownBy(() -> svc.decode("not.a.token"))
        .isInstanceOf(JwtException.class)
        .hasMessageContaining("Invalid token");
  }
}
