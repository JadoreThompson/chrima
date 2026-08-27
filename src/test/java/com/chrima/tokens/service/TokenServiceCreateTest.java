package com.chrima.tokens.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.tokens.api.dto.TokenResponse;
import com.chrima.tokens.api.enums.TokenChain;
import com.chrima.tokens.api.enums.TokenStandard;
import com.chrima.tokens.model.Token;
import org.junit.jupiter.api.Test;

class TokenServiceCreateTest extends AbstractTokenServiceIntegrationBase {

  @Test
  void shouldCreateTokenAndPersist() {
    TokenResponse token =
        tokenService.create("USDT", TokenStandard.ERC_20, TokenChain.ETH, "0xdAC17F958D2ee523a");

    assertThat(token.getId()).isNotNull();
    assertThat(token.getName()).isEqualTo("USDT");
    assertThat(token.getStandard()).isEqualTo(TokenStandard.ERC_20);
    assertThat(token.getChain()).isEqualTo(TokenChain.ETH);
    assertThat(token.getAddress()).isEqualTo("0xdAC17F958D2ee523a");

    Token row = tokenRepository.findById(token.getId()).orElseThrow();
    assertThat(row.getName()).isEqualTo("USDT");
    assertThat(row.getStandard()).isEqualTo(TokenStandard.ERC_20);
    assertThat(row.getChain()).isEqualTo(TokenChain.ETH);
    assertThat(row.getAddress()).isEqualTo("0xdAC17F958D2ee523a");
  }

  @Test
  void shouldCreateMultipleTokensWithDifferentAddresses() {
    TokenResponse eth =
        tokenService.create(
            "ETH",
            TokenStandard.ERC_20,
            TokenChain.ETH,
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE");
    TokenResponse usdc =
        tokenService.create(
            "USDC",
            TokenStandard.ERC_20,
            TokenChain.ETH,
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48");

    assertThat(eth.getId()).isNotEqualTo(usdc.getId());
    assertThat(tokenRepository.count()).isEqualTo(2);
  }

  @Test
  void shouldCreateTokenWithEthChainAndErc20Standard() {
    TokenResponse token =
        tokenService.create(
            "ETH",
            TokenStandard.ERC_20,
            TokenChain.ETH,
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE");

    assertThat(token.getStandard()).isEqualTo(TokenStandard.ERC_20);
    assertThat(token.getChain()).isEqualTo(TokenChain.ETH);
    assertThat(token.getStandard().getValue()).isEqualTo("erc-20");
    assertThat(token.getChain().getValue()).isEqualTo("ethereum");
  }
}
