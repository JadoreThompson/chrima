# Billing

Monetises the Chrima platform by managing user subscription checkouts and
cancellations through pluggable payment providers (e.g. Stripe).

Billing is **user-level**: each user pays for their own account tier
(`free` / `pro`). It does **not** touch workspace components — product, price,
discord and subscription packages are out of scope and must never be imported
from here.

## Dependencies

Allowed (only these):

- `chrima.user` — reading user, their tier and stored billing/customer ids
- `chrima.notification` — enqueuing subscription/billing notifications
- `chrima.event_bus` — publishing domain events through the outbox

Forbidden: `chrima.product`, `chrima.price`, `chrima.discord`,
`chrima.subscription`, and anything that models workspace components.

## Package layout

```
billing/
├── model.py          # Billing table (per-user subscription row)
├── schema.py         # Request/response DTOs
├── enums.py          # BillingProvider, BillingStatus
├── exception.py      # Domain exceptions
├── router.py         # /billing/* API endpoints incl. the webhook
├── service/
│   └── billing.py    # BillingService — orchestrates flows, talks to the DB
├── provider/
│   ├── base.py       # BillingProvider ABC
│   └── stripe.py     # StripeBillingProvider — talks to the Stripe API
└── listener/
    ├── base.py       # BillingWebhookListener ABC
    └── stripe.py     # StripeBillingWebhookListener — handles Stripe events
```

## Layers

- **Router** (`router.py`) exposes HTTP endpoints and wires them to the service
  and webhook listener.
- **Service** (`BillingService`) interacts with the **database** and composes
  provider + event publisher + notifications. It never calls the provider API
  directly beyond delegating to a provider.
- **Provider** (`StripeBillingProvider`) interacts with the **provider API**
  (Stripe). It is stateless regarding the DB.
- **Listener** (`StripeBillingWebhookListener`) interacts with the **database**
  to reconcile provider events (checkout completed, subscription deleted),
  verifies signatures, and publishes outbox events.
- **Event bus** carries `billing.*` events via the outbox to the Kafka
  `billing-events` topic.

## Data model

`Billing` (table `billing`) — one row per paying user:

| column             | type     | notes                         |
| ------------------ | -------- | ----------------------------- |
| `id`               | uuid PK  |                               |
| `user_id`          | uuid FK  | unique — one billing per user |
| `subscription_id`  | string   | provider subscription id      |
| `billing_provider` | string   | e.g. `stripe`                 |
| `customer_id`      | string   | provider customer id          |
| `created_at`       | datetime |                               |
| `updated_at`       | datetime | auto-updated                  |

The user row itself also carries `billing_provider` and `customer_id`
(managed through `UserService.get_billing` / `set_billing`).

## API

All endpoints under `/billing` (prefix `billing`).

### `POST /billing/checkout-session`

Creates a provider checkout session for the authenticated user's requested
tier.

- Auth: JWT (cookie)
- Body: `CreateCheckoutSessionRequest { tier }`
- Response: `CreateCheckoutSessionResponse { url }`

Flow: `BillingService.create_checkout_session` loads the user, asks the
provider for a checkout session with `{"user_id": ...}` metadata, stores a
`checkout_session:<id> -> <user_id>` mapping in Redis, and returns the
provider's hosted URL.

### `POST /billing/cancel-subscription`

Cancels the authenticated user's current provider subscription.

- Auth: JWT (cookie)
- Response: `200 OK`

Flow: `BillingService.cancel_subscription` looks up the user's billing row and
delegates `cancel_subscription(subscription_id)` to the provider. The
resulting provider `customer.subscription.deleted` event is reconciled by the
webhook listener.

### `POST /billing/webhook`

Ingests provider webhook events.

- No auth; the listener verifies the provider signature itself
- Body: raw provider event (JSON)
- Headers: raw headers so the listener can extract the signature header

Flow: `BillingWebhookListener.handle(headers, body, db_sess)` verifies the
signature, dedupes the event, updates the DB, and emits the relevant
`billing.*` event through the outbox.

## Provider contract

```python
class BillingProvider(ABC):
    async def create_checkout_session(self, tier: Tier, metadata=None) -> CheckoutSession: ...
    async def cancel_subscription(self, subscription_id: str) -> None: ...
```

Providers are constructed from config and are enabled only when the required
environment variables are present.

### Stripe

- Requires `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET` and a price id per tier
  (`STRIPE_PRO_PRICE_ID`).
- Uses EIP-independent standard Stripe Checkout (USDT/fiat handled upstream).
- `StripeBillingWebhookListener` must verify incoming webhooks with the Stripe
  signature header before processing.

## Configuration

| variable                        | default                                 | purpose                          |
| ------------------------------- | --------------------------------------- | -------------------------------- |
| `BILLING_PROVIDER`              | `stripe`                                | active provider                  |
| `BILLING_SUCCESS_URL`           | `http://localhost:3001/billing/success` | checkout success redirect        |
| `BILLING_CANCEL_URL`            | `http://localhost:3001/billing/cancel`  | checkout cancel redirect         |
| `STRIPE_API_KEY`                | `""`                                    | Stripe secret key                |
| `STRIPE_WEBHOOK_SECRET`         | —                                       | webhook signature secret         |
| `STRIPE_PRO_PRICE_ID`           | —                                       | Stripe price id for the PRO tier |
| `KAKFA_BILLING_EVENTS_TOPIC`    | `billing-events`                        | Kafka topic for billing events   |
| `REDIS_CHECKOUT_SESSION_PREFIX` | `checkout_session:`                     | Redis key prefix for sessions    |

## Events

Billing events flow through the standard outbox pipeline
(`OutboxEventPublisher` → `event_outbox` → `OutboxPoller` → Kafka) and use
the `KAKFA_BILLING_EVENTS_TOPIC` topic. A `billing.*` event type is expected
for checkout completion, renewal and cancellation so downstream consumers can
react without importing this package.

## Notifications

The service/listener may enqueue notifications via
`NotificationPublisher` (e.g. payment confirmation, subscription cancelled)
using the notification package's context models.
