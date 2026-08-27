package com.chrima.tokens.api;

import com.chrima.tokens.api.dto.TokenResponse;
import com.chrima.tokens.api.enums.TokenChain;
import com.chrima.tokens.api.enums.TokenStandard;
import java.util.List;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;

public interface ITokenService {

  TokenResponse create(String name, TokenStandard standard, TokenChain chain, String address);

  TokenResponse getById(UUID tokenId);

  Page<TokenResponse> getTokens(Pageable pageable);

  default Page<TokenResponse> getTokens(int page, int limit) {
    return getTokens(PageRequest.of(page - 1, limit));
  }

  List<TokenResponse> getByIds(List<UUID> tokenIds);
}
