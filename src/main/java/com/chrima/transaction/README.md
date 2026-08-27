# transaction

A `transaction` records a completed on-chain payment for a product at a specific price. The module is query-only:
it provides read access to persisted transactions (by id, sender, product, price, or workspace) and defines the
`TransactionCompletedEvent` emitted when a payment is recorded.

## Entry point

`api.ITransactionService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `events.api.IEventService` — `TransactionCompletedEvent` is published through the transactional outbox.

## Notes

- Transactions and their `eth_blocks` checkpoint records are persisted by the on-chain listener, which is not yet
  ported to this module; nothing in this module mutates state.
- The workspace filter resolves the owning workspace at query time by joining through `price_id`.
- `recipient` / `platform_user_id` are stored but intentionally not exposed by `TransactionResponse`.