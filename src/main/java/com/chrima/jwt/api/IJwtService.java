package com.chrima.jwt.api;

import jakarta.servlet.http.HttpServletResponse;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;

public interface IJwtService {

  String encode(UUID sub, String email, UUID workspaceId);

  Jwt decode(String token);

  Jwt decodeJwt(String token);

  /**
   * Encode and set HTTP-only cookie on the response.
   *
   * @return the generated token
   */
  String setCookie(HttpServletResponse response, UUID sub, String email, UUID workspaceId);

  void removeCookie(HttpServletResponse response);

  Jwt validate(String token);
}
