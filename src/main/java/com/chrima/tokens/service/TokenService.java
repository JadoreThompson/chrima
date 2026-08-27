package com.chrima.tokens.service;

import com.chrima.tokens.api.ITokenService;
import com.chrima.tokens.api.dto.TokenResponse;
import com.chrima.tokens.api.enums.TokenChain;
import com.chrima.tokens.api.enums.TokenStandard;
import com.chrima.tokens.exception.TokenNotFoundException;
import com.chrima.tokens.model.Token;
import com.chrima.tokens.repository.TokenRepository;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class TokenService implements ITokenService {

  private final TokenRepository tokenRepository;

  @Override
  @Transactional
  public TokenResponse create(
      String name, TokenStandard standard, TokenChain chain, String address) {
    log.info("Creating token name={} standard={} chain={}", name, standard, chain);
    Token token =
        Token.builder().name(name).standard(standard).chain(chain).address(address).build();
    Token saved = tokenRepository.saveAndFlush(token);
    log.info("Token created id={} name={}", saved.getId(), name);
    return TokenResponse.from(saved);
  }

  @Override
  @Transactional(readOnly = true)
  public TokenResponse getById(UUID tokenId) {
    Token token =
        tokenRepository
            .findById(tokenId)
            .orElseThrow(
                () -> {
                  log.warn("Token not found id={}", tokenId);
                  return new TokenNotFoundException(tokenId);
                });
    return TokenResponse.from(token);
  }

  @Override
  @Transactional(readOnly = true)
  public Page<TokenResponse> getTokens(Pageable pageable) {
    return tokenRepository.findAll(pageable).map(TokenResponse::from);
  }

  @Override
  @Transactional(readOnly = true)
  public List<TokenResponse> getByIds(List<UUID> tokenIds) {
    if (tokenIds == null || tokenIds.isEmpty()) {
      return Collections.emptyList();
    }
    return tokenRepository.findAllById(tokenIds).stream().map(TokenResponse::from).toList();
  }
}
