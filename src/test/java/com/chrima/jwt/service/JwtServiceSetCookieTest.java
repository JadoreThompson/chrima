package com.chrima.jwt.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.jwt.api.JwtPayload;
import com.chrima.jwt.config.JwtProperties;
import com.chrima.user.service.UserService;
import jakarta.servlet.http.Cookie;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockHttpServletResponse;

@ExtendWith(MockitoExtension.class)
class JwtServiceSetCookieTest {

  @Mock UserService userService;

  @Test
  void shouldSetCookieWithHttpOnly() {
    JwtProperties props = new JwtProperties();
    JwtService svc = new JwtService(props, userService);
    MockHttpServletResponse rsp = new MockHttpServletResponse();
    svc.setCookie(rsp, UUID.randomUUID(), "cookie@test.com", null);
    Cookie cookie = rsp.getCookie(props.getCookieAlias());
    assertThat(cookie).isNotNull();
    assertThat(cookie.isHttpOnly()).isTrue();
    assertThat(cookie.getSecure()).isEqualTo(props.isSecure());
    assertThat(cookie.getPath()).isEqualTo("/");
  }

  @Test
  void shouldSetCookieReturnsDecodableToken() {
    JwtProperties props = new JwtProperties();
    JwtService svc = new JwtService(props, userService);
    MockHttpServletResponse rsp = new MockHttpServletResponse();
    UUID sub = UUID.randomUUID();
    String token = svc.setCookie(rsp, sub, "return@test.com", null);
    Cookie cookie = rsp.getCookie(props.getCookieAlias());
    assertThat(cookie).isNotNull();
    assertThat(cookie.getValue()).isEqualTo(token);
    JwtPayload payload = svc.decode(token);
    assertThat(payload.getSubject()).isEqualTo(sub);
    assertThat(payload.getEmail()).isEqualTo("return@test.com");
  }
}
