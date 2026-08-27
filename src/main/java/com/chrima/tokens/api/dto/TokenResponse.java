package com.chrima.tokens.api.dto;

import com.chrima.tokens.api.enums.TokenChain;
import com.chrima.tokens.api.enums.TokenStandard;
import com.chrima.tokens.model.Token;
import java.util.UUID;
import lombok.Builder;
import lombok.Value;

@Value
@Builder
public class TokenResponse {
  UUID id;
  String name;
  TokenStandard standard;
  TokenChain chain;
  String address;

  public static TokenResponse from(Token token) {
    return TokenResponse.builder()
        .id(token.getId())
        .name(token.getName())
        .standard(token.getStandard())
        .chain(token.getChain())
        .address(token.getAddress())
        .build();
  }
}
