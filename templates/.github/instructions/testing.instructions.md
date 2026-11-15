---
applyTo: "**/*Test.java"
---
# Testing rules

- Follow the test framework and conventions already used by the repository.
- Test observable behavior, not private implementation details.
- Cover success, validation, boundary, exception, timeout, retry, and concurrency behavior as relevant.
- Use integration tests for database, messaging, serialization, and framework wiring boundaries.
- Avoid flaky sleeps; use deterministic synchronization and bounded timeouts.
- Do not mock the behavior that the test is intended to verify.
- Keep test data isolated and avoid production credentials or data.
