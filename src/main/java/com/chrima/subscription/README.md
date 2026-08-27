# subscription

A `SubscriptionBalance` tracks the credit a platform user has left on a product within an external group. The module
handles balance lifecycle (create, credit, cycle processing, cancel) and notifies on balance expiry.

## Entry point

`api.ISubscriptionService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).

## Dependencies

- `events.api.IEventService` — publishes `SubscriptionCancelledEvent` on cancel via the transactional outbox.
- `price.api` — `RecurringInterval` drives cycle processing.
- `workspace.api.IWorkspaceService` / `product.api.IProductService` — resolve context during expiry checks.
- `notification.discord.api.IDiscordNotificationService` — emits `subscription.expiring` / `subscription.expired` notifications.