package com.chrima.tokens.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.chrima.tokens.dto.TokenResponse;
import com.chrima.tokens.exception.TokenNotFoundException;
import com.chrima.tokens.model.enums.TokenChain;
import com.chrima.tokens.model.enums.TokenStandard;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class TokenServiceGetByIdTest extends AbstractTokenServiceIntegrationBase {

  @Test
  void shouldGetById() {
    TokenResponse created =
        tokenService.create("USDT", TokenStandard.ERC_20, TokenChain.ETH, "0xdAC17F958D2ee523a");

    TokenResponse fetched = tokenService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getName()).isEqualTo("USDT");
    assertThat(fetched.getStandard()).isEqualTo(TokenStandard.ERC_20);
    assertThat(fetched.getChain()).isEqualTo(TokenChain.ETH);
    assertThat(fetched.getAddress()).isEqualTo("0xdAC17F958D2ee523a");
  }

  @Test
  void shouldThrowWhenGetByIdNotFound() {
    UUID randomId = UUID.randomUUID();

    assertThatThrownBy(() -> tokenService.getById(randomId))
        .isInstanceOf(TokenNotFoundException.class)
        .satisfies(
            ex -> assertThat(((TokenNotFoundException) ex).getTokenId()).isEqualTo(randomId));
  }

  @Test
  void shouldGetByIdReturnsAllFields() {
    TokenResponse created =
        tokenService.create(
            "ETH",
            TokenStandard.ERC_20,
            TokenChain.ETH,
            "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE");

    TokenResponse fetched = tokenService.getById(created.getId());

    assertThat(fetched.getId()).isEqualTo(created.getId());
    assertThat(fetched.getName()).isEqualTo("ETH");
    assertThat(fetched.getAddress()).isEqualTo("0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE");
    assertThat(fetched.getStandard()).isEqualTo(TokenStandard.ERC_20);
    assertThat(fetched.getChain()).isEqualTo(TokenChain.ETH);
  }
}
