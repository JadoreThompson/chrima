package com.chrima.jwt.api;

import com.chrima.jwt.api.dto.JwtPayload;
import jakarta.servlet.http.HttpServletResponse;
import java.util.UUID;

public interface IJwtService {

  String encode(UUID sub, String email, UUID workspaceId);

  JwtPayload decode(String token);

  JwtPayload decodeJwt(String token);

  /**
   * Encode and set HTTP-only cookie on the response.
   *
   * @return the generated token
   */
  String setCookie(HttpServletResponse response, UUID sub, String email, UUID workspaceId);

  void removeCookie(HttpServletResponse response);

  JwtPayload validate(String token);
}
