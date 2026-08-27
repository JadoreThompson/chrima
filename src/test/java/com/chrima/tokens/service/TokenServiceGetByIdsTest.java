package com.chrima.tokens.service;

import static org.assertj.core.api.Assertions.assertThat;

import com.chrima.tokens.api.dto.TokenResponse;
import com.chrima.tokens.api.enums.TokenChain;
import com.chrima.tokens.api.enums.TokenStandard;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class TokenServiceGetByIdsTest extends AbstractTokenServiceIntegrationBase {

  @Test
  void shouldGetByIdsReturnsMatchingTokens() {
    TokenResponse eth =
        tokenService.create(
            "ETH",
            TokenStandard.ERC_20,
            TokenChain.ETH,
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE");
    TokenResponse usdt =
        tokenService.create("USDT", TokenStandard.ERC_20, TokenChain.ETH, "0xdAC17F958D2ee523a");
    tokenService.create(
        "USDC", TokenStandard.ERC_20, TokenChain.ETH, "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48");

    List<TokenResponse> result = tokenService.getByIds(List.of(eth.getId(), usdt.getId()));

    assertThat(result).hasSize(2);
    assertThat(result)
        .extracting(TokenResponse::getId)
        .containsExactlyInAnyOrder(eth.getId(), usdt.getId());
  }

  @Test
  void shouldGetByIdsReturnsEmptyWhenInputEmpty() {
    tokenService.create("ETH", TokenStandard.ERC_20, TokenChain.ETH, "0x1");

    List<TokenResponse> result = tokenService.getByIds(Collections.emptyList());

    assertThat(result).isEmpty();
  }

  @Test
  void shouldGetByIdsReturnsEmptyWhenInputNull() {
    tokenService.create("ETH", TokenStandard.ERC_20, TokenChain.ETH, "0x1");

    List<TokenResponse> result = tokenService.getByIds(null);

    assertThat(result).isEmpty();
  }

  @Test
  void shouldGetByIdsIgnoresNonExistentIds() {
    TokenResponse eth = tokenService.create("ETH", TokenStandard.ERC_20, TokenChain.ETH, "0x1");

    List<TokenResponse> result = tokenService.getByIds(List.of(eth.getId(), UUID.randomUUID()));

    assertThat(result).hasSize(1);
    assertThat(result.get(0).getId()).isEqualTo(eth.getId());
  }

  @Test
  void shouldGetByIdsReturnsEmptyWhenNoMatch() {
    tokenService.create("ETH", TokenStandard.ERC_20, TokenChain.ETH, "0x1");

    List<TokenResponse> result =
        tokenService.getByIds(List.of(UUID.randomUUID(), UUID.randomUUID()));

    assertThat(result).isEmpty();
  }

  @Test
  void shouldGetByIdsReturnsAllWhenAllMatch() {
    TokenResponse eth = tokenService.create("ETH", TokenStandard.ERC_20, TokenChain.ETH, "0x1");
    TokenResponse usdt = tokenService.create("USDT", TokenStandard.ERC_20, TokenChain.ETH, "0x2");
    TokenResponse usdc = tokenService.create("USDC", TokenStandard.ERC_20, TokenChain.ETH, "0x3");

    List<TokenResponse> result =
        tokenService.getByIds(List.of(eth.getId(), usdt.getId(), usdc.getId()));

    assertThat(result).hasSize(3);
  }
}
