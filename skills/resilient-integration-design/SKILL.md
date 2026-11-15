---
name: resilient-integration-design
description: Design safe API, messaging, retry, timeout, and idempotency behavior.
---

# Resilient Integration Design

Map producer/consumer ownership, persistence guarantees, transaction boundaries, delivery semantics,
timeouts, retries, backoff, jitter, circuit breakers, bulkheads, dead-letter handling, ordering,
deduplication, idempotency keys, replay, and observability. Distinguish in-process events from durable
cross-process messaging. For multi-instance workloads, analyze duplicate execution and coordination.
Do not claim exactly-once delivery without defining and proving the end-to-end guarantees.

