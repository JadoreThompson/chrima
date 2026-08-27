# tokens — blockchain token registry

Reference implementation: `chrima-backend/src/chrima/tokens`.

## Entry point

`api.ITokenService` — `OPEN` module (`api._PackageInfo`). Methods mirror `chrima.tokens.service.TokenService` from the Python backend.

## Service

- `create(name, standard, chain, address)` — persists `Token` and returns `TokenResponse`.
- `getById(tokenId)` — throws `TokenNotFoundException` when missing (mirrors Python `TokenNotFoundException`).
- `getTokens(pageable)` / `getTokens(page, limit)` — Spring `Page<TokenResponse>` via `Pageable` (`PageRequest.of(page-1, limit)`), delegates to `TokenRepository.findAll(pageable)`; mirrors Python `get_tokens(page, limit)` paginated response (Python uses `limit+1` / `has_next` probe).
- `getByIds(tokenIds)` — returns empty list for null/empty input; mirrors Python `get_by_ids`.

## Seeder

- `service.TokenSeeder` — seeds ETH, USDT, USDC on `TokenChain.ETH` / `TokenStandard.ERC_20` with network-specific addresses from `TOKEN_ADDRESSES` (mainnet vs sepolia). Mirrors Python `TokenSeeder` + `TOKEN_ADDRESSES` dict. Default `run()` uses sepolia (`mainnet=false`).

## Model

- `model.Token` — JPA `@Entity` (`tokens`), `UUID id`, `name`, `standard` (`TokenStandard` enum), `chain` (`TokenChain` enum), `address`. Pattern: `@Getter` + `@Builder` + `@AllArgsConstructor(access = AccessLevel.PACKAGE)` + protected no-arg constructor.
- `model.enums.TokenChain` — `ETH("ethereum")`.
- `model.enums.TokenStandard` — `ERC_20("erc-20")`.

## Where to look

`api/` contract · `model/` entity + enums · `dto/` response · `service/` implementation + seeder · `exception/` not-found · `repository/` Spring Data JPA
