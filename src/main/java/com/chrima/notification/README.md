# notification — transactional outbox for external dispatches

Durable, idempotent enqueue → poll → dispatch. Callers never send directly; they persist JSON and a scheduled poller delivers via `INotificationChannel`.

## Entry points

| Call | What it does |
|------|--------------|
| `api.INotificationService.publish(recipient, ChannelType, INotificationContent, idempotencyKey)` | Validates (email format when `EMAIL`), dedups on `idempotencyKey` (unique), serializes `content` to `notifications.content` as `PENDING`. Throws `IllegalArgumentException` / `IOException`. |
| `discord.api.IDiscordNotificationService.publish(guildId, channelId, type, IDiscordNotificationContent, idempotencyKey)` | Same pattern for Discord. Persists to `discord_notifications` (`type` = discriminator for deserialization). |

Both modules are `OPEN` (`api._PackageInfo`) — other modulith modules may depend on `api` only.

## Happy path

```
publish() -> Notification/DiscordNotification (PENDING, attempts=0)
           -> *Poller @Scheduled(fixedDelay) batches PENDING (Pageable)
           -> resolves INotificationChannel / DiscordNotificationChannel -> dispatch
           -> COMPLETED (dispatchedAt set) | retry on exception
```

- `service.NotificationPoller` — `notification.polling.delay` / `batch-size` / `max-attempts` (default 100/3). Deserializes via `ObjectMapper` per `ChannelType`; dispatches through `List<INotificationChannel<?>>#supports`.
- `discord.service.DiscordNotificationPoller` — `discord.polling.*` (`@ConditionalOnProperty discord.token`), resolves content class via `DiscordNotificationContentRegistry` (classpath scan for `@DiscordNotificationType`), sends via `DiscordNotificationChannel` (JDA `TextChannel#sendMessageEmbeds`, nonce = `DiscordNonce.from(idempotencyKey)` for Discord dedup).
- `events` equivalent uses Kafka; this package uses SES / JDA directly.

## Channels (extensibility)

- `channel.INotificationChannel<T extends INotificationContent>` — implement `supports(ChannelType)` + `dispatch(recipient, T)`.
- Current: `EmailNotificationChannel` (`ChannelType.EMAIL`, AWS SES `SesClient`, `aws.ses.from`).
- Discord: `discord.api.IDiscordNotificationBuilder<T>` — implement `supports(Class)` + `build(T)->MessageEmbed`; auto-discovered as Spring beans, selected by `DiscordNotificationChannel`.

Add a channel: new `ChannelType` value + `INotificationChannel` bean (+ content class + poller branch).

## Failure & DLQ

After `maxAttempts` → `FAILED` + `dlq.DeadLetterService.enqueue()` / `discord.dlq.DiscordDeadLetterService.enqueue()` copies row to `dead_letter_notifications` / `discord_dead_letter_notifications` with `failureReason`, `nextAttemptAt = now + initialDelay`.

- `dlq.DeadLetterPoller` / `discord.dlq.DiscordDeadLetterPoller` — `@Scheduled ${notification.dlq.polling-delay:5000}` / `${discord.dlq.*}`, queries `findReady(now)`, re-dispatches via same channel abstraction, exponential backoff `initialDelay * multiplier^(attempts-1)` → `COMPLETED` or `FAILED` (terminal). `calculateNextAttempt(attempts)` is test-visible.

## Model

- `model.Notification` / `discord.model.DiscordNotification` — JPA `@Entity`, `UUID id`, `content TEXT (JSON)`, `idempotencyKey unique`, `status PENDING|COMPLETED|FAILED`, `attempts`, `lastAttemptedAt`, `dispatchedAt` (+ `discordMessageId` for Discord). `markDispatched()` sets timestamp.
- Registries: `DiscordNotificationContentRegistry` scans `com.chrima` for `@DiscordNotificationType` → `Map<type, Class>`.

## Where to look

`api/` public contract · `service/` enqueue+poller · `channel/` transport · `dlq/` retry · `discord/` parallel stack (api/model/channel/service/dlq)
