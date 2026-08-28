package com.chrima.jwt.api.dto;

import java.time.Instant;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class JwtPayload {
  UUID sub;
  String email;
  Instant exp;
  UUID workspaceId;

  /** Expiry as epoch seconds, mirroring Python's float timestamp. */
  public long expEpochSeconds() {
    return exp.getEpochSecond();
  }

  public double expAsDouble() {
    return exp.toEpochMilli() / 1000.0;
  }
}
