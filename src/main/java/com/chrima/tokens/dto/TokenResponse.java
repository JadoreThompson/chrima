package com.chrima.tokens.dto;

import com.chrima.tokens.model.enums.TokenChain;
import com.chrima.tokens.model.enums.TokenStandard;
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
