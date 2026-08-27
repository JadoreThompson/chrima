package com.chrima.tokens.api.dto;

import com.chrima.tokens.api.enums.TokenChain;
import com.chrima.tokens.api.enums.TokenStandard;
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
}
