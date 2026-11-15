---
applyTo: "**/*.java"
---
# Java engineering rules

- Match the repository's configured Java language level; do not use newer syntax or APIs without verifying compatibility.
- Prefer immutable values, explicit ownership, clear interfaces, and composition.
- Consider nullability, exception semantics, resource closure, interrupt preservation, and thread safety.
- Use try-with-resources for closeable resources.
- Avoid static mutable state, unbounded caches, unbounded queues, and unmanaged executors.
- Preserve interruption when catching InterruptedException.
- Avoid swallowing exceptions or returning misleading defaults.
- Keep methods cohesive and avoid unnecessary generic frameworks.
- Add tests for boundary conditions, concurrency, failure paths, and resource cleanup.
