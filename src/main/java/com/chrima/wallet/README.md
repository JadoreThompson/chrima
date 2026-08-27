# wallet

A `wallet` is a workspace-scoped on-chain address used as a payout/fulfilment target by products. The module
provides workspace-scoped CRUD over these wallets and their associated tokens.

## Entry point

`api.IWalletService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `workspace.api.IWorkspaceService` — validates that the owning workspace exists before a wallet is created.