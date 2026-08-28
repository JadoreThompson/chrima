package com.chrima.jwt.api;

import java.time.Instant;
import java.util.UUID;
import org.springframework.security.oauth2.jwt.Jwt;

/**
 * Typed view over a validated {@link Jwt}, centralising claim-to-type conversions.
 *
 * <p>Exposes the identity claims ({@code sub}, {@code em}, {@code workspace_id}) as their native
 * Java types so callers never have to parse {@code String} claims themselves.
 */
public final class JwtPayload {

  private static final String EMAIL_CLAIM = "em";
  private static final String WORKSPACE_ID_CLAIM = "workspace_id";

  private final Jwt jwt;

  private JwtPayload(Jwt jwt) {
    this.jwt = jwt;
  }

  /** Wraps a decoded {@link Jwt} in a typed payload. */
  public static JwtPayload from(Jwt jwt) {
    return new JwtPayload(jwt);
  }

  /** The authenticated user's id (from the {@code sub} claim). */
  public UUID getSubject() {
    return UUID.fromString(jwt.getSubject());
  }

  /** The authenticated user's email (from the {@code em} claim). */
  public String getEmail() {
    return jwt.getClaimAsString(EMAIL_CLAIM);
  }

  /** The selected workspace id (from the {@code workspace_id} claim), or {@code null}. */
  public UUID getWorkspaceId() {
    String workspaceId = jwt.getClaimAsString(WORKSPACE_ID_CLAIM);
    return workspaceId != null ? UUID.fromString(workspaceId) : null;
  }

  /** The token expiration time. */
  public Instant getExpiresAt() {
    return jwt.getExpiresAt();
  }

  /** The raw token value. */
  public String getTokenValue() {
    return jwt.getTokenValue();
  }
}
