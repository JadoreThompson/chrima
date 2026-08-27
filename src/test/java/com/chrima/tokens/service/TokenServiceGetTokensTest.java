package com.chrima.tokens.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.tokens.dto.TokenResponse;
import com.chrima.tokens.model.enums.TokenChain;
import com.chrima.tokens.model.enums.TokenStandard;
import org.junit.jupiter.api.Test;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;

class TokenServiceGetTokensTest extends AbstractTokenServiceIntegrationBase {

  @Test
  void shouldListTokensReturnsAll() {
    TokenResponse eth =
        tokenService.create(
            "ETH",
            TokenStandard.ERC_20,
            TokenChain.ETH,
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE");
    TokenResponse usdt =
        tokenService.create("USDT", TokenStandard.ERC_20, TokenChain.ETH, "0xdAC17F958D2ee523a");
    TokenResponse usdc =
        tokenService.create(
            "USDC",
            TokenStandard.ERC_20,
            TokenChain.ETH,
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48");

    Page<TokenResponse> result = tokenService.getTokens(PageRequest.of(0, 10));

    assertThat(result.getContent()).hasSize(3);
    assertThat(result.getContent())
        .extracting(TokenResponse::getId)
        .containsExactlyInAnyOrder(eth.getId(), usdt.getId(), usdc.getId());
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldPaginateFirstPage() {
    for (int i = 0; i < 3; i++) {
      tokenService.create("TOKEN-" + i, TokenStandard.ERC_20, TokenChain.ETH, "0xaddr" + i);
    }

    Page<TokenResponse> result = tokenService.getTokens(PageRequest.of(0, 2));

    assertThat(result.getContent()).hasSize(2);
    assertThat(result.hasNext()).isTrue();
    assertThat(result.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldPaginateSecondPage() {
    for (int i = 0; i < 3; i++) {
      tokenService.create("TOKEN-" + i, TokenStandard.ERC_20, TokenChain.ETH, "0xaddr" + i);
    }

    Page<TokenResponse> page1 = tokenService.getTokens(PageRequest.of(0, 2));
    Page<TokenResponse> page2 = tokenService.getTokens(PageRequest.of(1, 2));

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
    assertThat(page2.getTotalElements()).isEqualTo(3);
  }

  @Test
  void shouldReturnEmptyWhenNoTokens() {
    Page<TokenResponse> result = tokenService.getTokens(PageRequest.of(0, 10));

    assertThat(result.getContent()).isEmpty();
    assertThat(result.hasNext()).isFalse();
    assertThat(result.getTotalElements()).isEqualTo(0);
  }

  @Test
  void shouldSupportLegacyPageAndLimitOverload() {
    for (int i = 0; i < 3; i++) {
      tokenService.create("TOKEN-" + i, TokenStandard.ERC_20, TokenChain.ETH, "0xaddr" + i);
    }

    Page<TokenResponse> page1 = tokenService.getTokens(1, 2);
    Page<TokenResponse> page2 = tokenService.getTokens(2, 2);

    assertThat(page1.getContent()).hasSize(2);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }

  @Test
  void shouldPaginateWithPageOneLimitOneMatchesPythonDefaults() {
    tokenService.create("ETH", TokenStandard.ERC_20, TokenChain.ETH, "0x1");
    tokenService.create("USDT", TokenStandard.ERC_20, TokenChain.ETH, "0x2");

    Page<TokenResponse> page1 = tokenService.getTokens(1, 1);
    Page<TokenResponse> page2 = tokenService.getTokens(2, 1);

    assertThat(page1.getContent()).hasSize(1);
    assertThat(page1.hasNext()).isTrue();
    assertThat(page2.getContent()).hasSize(1);
    assertThat(page2.hasNext()).isFalse();
  }
}
