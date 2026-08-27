# product

A `product` is a workspace-scoped sellable item that references a wallet for on-chain payouts/fulfilment. The module
provides workspace-scoped CRUD over these products.

## Entry point

`api.IProductService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `workspace.api.IWorkspaceService` — validates that the owning workspace exists before a product is created.
- `wallet.api.IWalletService` — validates that the referenced payout wallet exists.