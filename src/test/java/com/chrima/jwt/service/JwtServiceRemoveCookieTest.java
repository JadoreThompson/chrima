package com.chrima.jwt.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.jwt.config.JwtProperties;
import com.chrima.user.service.UserService;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mock.web.MockHttpServletResponse;

@ExtendWith(MockitoExtension.class)
class JwtServiceRemoveCookieTest {

  @Mock UserService userService;

  @Test
  void shouldRemoveCookieSetsMaxAgeZero() {
    JwtProperties props = new JwtProperties();
    JwtService svc = new JwtService(props, userService);
    MockHttpServletResponse rsp = new MockHttpServletResponse();
    svc.removeCookie(rsp);
    Cookie cookie = rsp.getCookie(props.getCookieAlias());
    assertThat(cookie).isNotNull();
    assertThat(cookie.getMaxAge()).isZero();
    assertThat(cookie.getValue()).isEqualTo("");
  }
}
