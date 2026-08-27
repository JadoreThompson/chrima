# events

Transactional outbox to Kafka: producers publish `IEventPayload`s instead of touching Kafka directly. Payloads are
persisted to an outbox, a scheduled poller publishes them to their registered topic, and failures are retried through
a dead-letter queue.

## Entry point

`api.IEventService` — `OPEN` module (`api` is marked `ApplicationModule.Type.OPEN`).