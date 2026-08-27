# subscription — per-user subscription balances for products

A `SubscriptionBalance` tracks how much credit a platform user (`platform_user_id`) has left on a
`product` for a given external group (`external_id`). Mirrors `chrima.subscription` from the Python backend.

## Entry point

`api.ISubscriptionService` — `OPEN` module (`api._PackageInfo`). Methods mirror `chrima.subscription.service.subscription.SubscriptionBalanceService`.

## Service

- `get(externalId, platformUserId, productId)` — looks up by the unique `(external_id, platform_user_id, product_id)` group; throws `SubscriptionBalanceNotFoundException` when missing.
- `getById(subscriptionBalanceId)` — throws `SubscriptionBalanceNotFoundException` when missing.
- `listByUserGroup(userId, externalId)` — all balances for a platform user within an external group (ids compared as strings).
- `create(externalId, platformUserId, productId, creditAmount, status, cycleStart, cycleEnd, lastProcessedTx)` — persists a new balance; `attemptCount` starts at `0`.
- `increaseBalance(externalId, platformUserId, productId, amount, transactionId)` — validates `amount > 0` and non-null `transactionId` (`SubscriptionBalanceValidationException`), credits `credit_amount`, updates `last_processed_tx`.
- `processCycle(externalId, platformUserId, productId, amount, recurringInterval, recurringIntervalCount, transactionId)` — debits `credit_amount`, sets `cycle_start = now`, `cycle_end = now + DAY/MONTH seconds * count` (`price.api.enums.RecurringInterval`), updates `last_processed_tx`.
- `cancel(subscriptionBalanceId)` — sets status `CANCELLED` (already-cancelled → `SubscriptionBalanceAlreadyCancelledException`), publishes `SubscriptionCancelledEvent`.

## Expiry checker

`service.SubscriptionExpiryChecker` — `@Scheduled` (`subscription.expiry.*`, defaults 1h interval, 6h
notification cooldown, 12h expiry window, `maxAttempts=2`). `@ConditionalOnProperty subscription.expiry.enabled`
(default `true`). Picks up balances via `SubscriptionBalanceRepository.findDueForExpiryCheck` (expiring-now /
already-expired, not cancelled, under attempt cap, outside cooldown), resolves product + workspace, publishes a
Discord notification (`subscription.expiring` / `subscription.expired`) via `notification.discord.api.IDiscordNotificationService`,
and increments `attemptCount` / sets `lastNotifiedAt` (marking expired balances `EXPIRED`).

## Event

- `event.SubscriptionCancelledEvent` — `IEventPayload` annotated `@EventType(value = "subscription.cancelled", topic = "subscription-events")` with `subscriptionBalanceId` + `externalId` + `platformUserId` + `productId`; published on cancel via `events.api.IEventService.publish` (transactional outbox → Kafka). Mirrors Python `SubscriptionCancelledEvent`.

## Model

- `model.SubscriptionBalance` — JPA `@Entity` (`subscription_balances`), `UUID id`, `externalId` (column `external_id`), `platformUserId` (column `platform_user_id`), `productId` (column `product_id`, ownership by id — no cross-module entity reference), `creditAmount` (column `credit_amount`, `double`), `cycleStart` / `cycleEnd` / `lastNotifiedAt` (`Integer` epoch seconds, nullable), `status` (`api.enums.SubscriptionStatus` ACTIVE/EXPIRED/CANCELLED/INCOMPLETE as `VARCHAR`), `lastProcessedTx` (column `last_processed_tx`, nullable), `attemptCount` (column `attempt_count`, default `0`), `createdAt` (`@CreationTimestamp`) / `updatedAt` (`@UpdateTimestamp`). Unique constraint `uq_subscription_balances_group_user_product` on `(external_id, platform_user_id, product_id)`.
- `notification/` — Discord notification content records (`SubscriptionExpiringNotificationContent` / `SubscriptionExpiredNotificationContent`, `@DiscordNotificationType subscription.expiring|expired`) + `SubscriptionNotificationBuilder` (`IDiscordNotificationBuilder`). Registered automatically by `DiscordNotificationContentRegistry`.

## Where to look

`api/` contract + response + enums · `model/` entity · `service/` implementation + expiry checker · `event/` payload · `exception/` not-found / already-cancelled / validation · `repository/` Spring Data JPA · `config/` expiry properties · `notification/` Discord content + builder