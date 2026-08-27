package com.chrima.tokens.service;

import com.chrima.tokens.api.ITokenService;
import com.chrima.tokens.api.dto.TokenResponse;
import com.chrima.tokens.api.enums.TokenChain;
import com.chrima.tokens.api.enums.TokenStandard;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class TokenSeeder {

  private final ITokenService tokenService;

  private static final Map<String, Map<String, String>> TOKEN_ADDRESSES =
      Map.of(
          "ETH",
              Map.of(
                  "mainnet", "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
                  "sepolia", "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"),
          "USDT",
              Map.of(
                  "mainnet", "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                  "sepolia", "0xaA8E23Fb1079EA71e0a56F48a2aA51851D843BE0"),
          "USDC",
              Map.of(
                  "mainnet", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                  "sepolia", "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"));

  /**
   * Seeds ETH, USDT, USDC tokens for the given network. Mirrors Python {@code
   * TokenSeeder.run(db_sess)}.
   *
   * @param mainnet true for mainnet addresses, false for sepolia
   * @return list of created TokenResponses
   */
  public List<TokenResponse> run(boolean mainnet) {
    String network = mainnet ? "mainnet" : "sepolia";
    List<SeedEntry> entries =
        List.of(
            new SeedEntry("ETH", TokenStandard.ERC_20, TokenChain.ETH),
            new SeedEntry("USDT", TokenStandard.ERC_20, TokenChain.ETH),
            new SeedEntry("USDC", TokenStandard.ERC_20, TokenChain.ETH));
    List<TokenResponse> tokens = new ArrayList<>();
    for (SeedEntry entry : entries) {
      log.info("Seeding token {}", entry.name());
      String address = TOKEN_ADDRESSES.get(entry.name()).get(network);
      TokenResponse token =
          tokenService.create(entry.name(), entry.standard(), entry.chain(), address);
      tokens.add(token);
    }
    return tokens;
  }

  /** Convenience overload defaulting to sepolia (mainnet=false), matching Python default. */
  public List<TokenResponse> run() {
    return run(false);
  }

  private record SeedEntry(String name, TokenStandard standard, TokenChain chain) {}
}
