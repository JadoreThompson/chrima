# events — transactional outbox to Kafka

Durable, idempotent `IEventPayload` → `event_outbox` → Kafka. Producers never touch Kafka directly; a poller publishes.

## Entry point

`api.IEventService.publish(eventType, IEventPayload, idempotencyKey)` — `OPEN` module (`api._PackageInfo`).

Validates `eventType` non-blank + registered in `EventTopicRegistry`, `idempotencyKey` non-blank, `payload != null`;
dedups on `idempotencyKey` (unique); serializes payload via `ObjectMapper` → `EventOutbox(PENDING)` (`api.EventType`
scan). Throws `IllegalArgumentException` / `IOException`.

## Defining an event

```java

@EventType(value = "order.created", topic = "orders")
public class OrderCreated implements IEventPayload { ...
}
```

`model.EventTopicRegistry` classpath-scans `com.chrima` for `@EventType` at startup → `Map<eventType, topic>`;
`register()` / `getTopic()` / `contains()` (duplicate `value` → `IllegalStateException`).

## Happy path

```
publish() -> EventOutbox (PENDING, attempts=0, payload=JSON)
          -> service.EventPoller @Scheduled(${events.polling.delay:5000}) batch PENDING
          -> kafka.EventKafkaPublisher.publish(EventOutbox)
          -> COMPLETED (dispatchedAt set) | retry
```

- `service.EventPoller` — `EventPollingProperties` (`batchSize`, `maxAttempts`), `findPending(PageRequest)`, delegates
  to `EventKafkaPublisher`, increments `attempts`/`lastAttemptedAt`; on `attempts >= maxAttempts` → `FAILED` + DLQ.
- `kafka.EventKafkaPublisher` — resolves topic via registry, sends `ProducerRecord(topic, idempotencyKey, payload)` with
  headers `eventType`, `idempotencyKey`, `eventId` (if present), `KafkaTemplate.send().get(10, TimeUnit.SECONDS)`.
  Overloads for `EventOutbox` / `EventDeadLetter`.

## Failure & DLQ

`dlq.EventDeadLetterService.enqueue(EventOutbox, failureReason)` copies to `event_dead_letters` (`eventOutboxId`,
`eventType`, `payload`, `failureReason`, `nextAttemptAt = now + initialDelay`, `PENDING`).

`dlq.EventDeadLetterPoller` — `@Scheduled(${events.dlq.polling-delay:5000})`, `findReady(now, Pageable)`, re-publishes
via `EventKafkaPublisher`, exponential backoff `initialDelay * multiplier^(attempts-1)` (`EventDeadLetterProperties`:
`batchSize`, `maxAttempts`, `initialDelay`, `backoffMultiplier`) → `COMPLETED` or terminal `FAILED`.
`calculateNextAttempt(attempts[, now])`.

## Model

- `model.EventOutbox` / `dlq.model.EventDeadLetter` — JPA `@Entity` (`event_outbox` / `event_dead_letters`), `UUID id`,
  `eventType`, `payload TEXT (JSON)`, `idempotencyKey`, `status PENDING|COMPLETED|FAILED` (`enums.EventStatus` /
  `dlq.model.enums.EventDeadLetterStatus`), `attempts`, `lastAttemptedAt`, `dispatchedAt`, `nextAttemptAt` (DLQ),
  `markDispatched()`.

## Where to look

`api/` contract+annotation · `model/` outbox+registry · `service/` enqueue+poller · `kafka/` publisher · `dlq/` retry
