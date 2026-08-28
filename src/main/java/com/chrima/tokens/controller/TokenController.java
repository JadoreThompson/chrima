package com.chrima.tokens.controller;

import com.chrima.jwt.api.IJwtService;
import com.chrima.tokens.api.ITokenService;
import com.chrima.tokens.api.dto.TokenResponse;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CookieValue;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Token controller exposing token-scoped endpoints.
 *
 * <p>Mirrors {@code chrima-backend/src/chrima/tokens/router.py}.
 */
@Slf4j
@RestController
@RequestMapping("/tokens")
@RequiredArgsConstructor
public class TokenController {

  private final ITokenService tokenService;
  private final IJwtService jwtService;

  @GetMapping("/{tokenId}")
  public ResponseEntity<TokenResponse> getToken(
      @PathVariable UUID tokenId,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    jwtService.validate(token);
    return ResponseEntity.ok(tokenService.getById(tokenId));
  }

  @GetMapping
  public ResponseEntity<Page<TokenResponse>> listTokens(
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "10") int limit,
      @CookieValue(value = "${jwt.cookie-alias:chrima-cookie}", required = false) String token) {
    jwtService.validate(token);
    return ResponseEntity.ok(tokenService.getTokens(page, limit));
  }
}
