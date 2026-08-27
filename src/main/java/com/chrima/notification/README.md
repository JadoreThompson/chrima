# notification

Transactional outbox for external dispatch: callers persist serialized content instead of sending directly, and
scheduled pollers deliver it through pluggable `INotificationChannel` implementations. Failed deliveries are retried
via a dead-letter queue. The module is split into a general stack (email via SES) and a parallel `discord` stack
(embeds via JDA).

## Entry points

- `api.INotificationService` — general notifications; `api` is marked `ApplicationModule.Type.OPEN`.
- `discord.api.IDiscordNotificationService` — Discord notifications; `discord.api` is marked
  `ApplicationModule.Type.OPEN`.
