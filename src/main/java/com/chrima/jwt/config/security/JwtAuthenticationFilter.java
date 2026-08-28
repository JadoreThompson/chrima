package com.chrima.jwt.config.security;

import com.chrima.jwt.api.IJwtService;
import com.chrima.jwt.api.JwtPayload;
import com.chrima.jwt.config.JwtProperties;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Authenticates requests by extracting a JWT from an HTTP-only cookie.
 *
 * <p>Mirrors Python's {@code depends_jwt} in {@code chrima-backend/src/chrima/api/deps.py}:
 *
 * <pre>
 * token = req.cookies.get(COOKIE_ALIAS)
 * if not token:
 *     raise JWTException("Not authenticated")
 * jwt_service.validate_jwt(token, db_sess)
 * </pre>
 *
 * <p>On success a {@link UsernamePasswordAuthenticationToken} with principal {@link JwtPayload} is
 * stored in the {@link SecurityContextHolder}. On failure the context is cleared and the request
 * continues unauthenticated — the {@code SecurityFilterChain} will then reject it with 401 for
 * protected endpoints.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

  private final JwtProperties jwtProperties;
  private final IJwtService jwtService;

  @Override
  protected void doFilterInternal(
      HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
      throws ServletException, IOException {
    String token = extractToken(request);
    if (token != null && !token.isBlank()) {
      try {
        JwtPayload payload = jwtService.validate(token);
        UsernamePasswordAuthenticationToken authentication =
            new UsernamePasswordAuthenticationToken(
                payload, null, List.of(new SimpleGrantedAuthority("ROLE_USER")));
        SecurityContextHolder.getContext().setAuthentication(authentication);
        log.debug(
            "Authenticated request sub={} path={}", payload.getSubject(), request.getRequestURI());
      } catch (Exception ex) {
        log.debug("Invalid JWT for path {}: {}", request.getRequestURI(), ex.getMessage());
        SecurityContextHolder.clearContext();
      }
    }
    filterChain.doFilter(request, response);
  }

  private String extractToken(HttpServletRequest request) {
    Cookie[] cookies = request.getCookies();
    if (cookies == null) {
      return null;
    }
    String alias = jwtProperties.getCookieAlias();
    for (Cookie cookie : cookies) {
      if (alias.equals(cookie.getName())) {
        return cookie.getValue();
      }
    }
    return null;
  }
}
