---
name: memory-leak-investigation
description: Investigate Java heap retention, GC pressure, and resource leaks with evidence.
---

# Memory and GC Investigation

Do not equate high heap usage with a memory leak. Establish workload, heap trend after GC,
allocation rate, GC pauses, old-generation occupancy, and container limits. Inspect caches,
static collections, listeners, ThreadLocal, executor queues, scheduled tasks, classloaders,
buffers, streams, JDBC resources, and client lifecycle. Static analysis produces hypotheses only.
Recommend JFR, GC logs, heap dumps, dominator tree, retained-size analysis, thread dumps, and
reproduction/load tests where available. State what evidence proves or disproves each hypothesis.

