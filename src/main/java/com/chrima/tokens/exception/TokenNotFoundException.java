package com.chrima.tokens.exception;

import java.util.UUID;

public class TokenNotFoundException extends RuntimeException {

  private final UUID tokenId;

  public TokenNotFoundException(UUID tokenId) {
    super("Token not found");
    this.tokenId = tokenId;
  }

  public UUID getTokenId() {
    return tokenId;
  }
}
