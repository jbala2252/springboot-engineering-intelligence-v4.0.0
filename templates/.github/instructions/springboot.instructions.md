---
applyTo: "**/*.{java,yml,yaml,properties,xml}"
---
# Spring and Spring Boot engineering rules

- Detect the actual Spring Boot and Spring Framework versions before using APIs or properties.
- Follow existing dependency-management conventions; avoid overriding managed versions without evidence.
- Prefer constructor injection and explicit configuration.
- Keep controllers thin; place business rules in appropriate application/domain services.
- Define transaction boundaries deliberately; understand proxy/self-invocation behavior.
- Configure timeouts, bounded retries, pool sizes, and resource limits explicitly where relevant.
- Consider startup/shutdown lifecycle, graceful termination, health/readiness, metrics, and tracing.
- Review scheduler overlap, multi-instance execution, idempotency, and distributed coordination.
- Do not assume in-process Spring events are durable or cross-instance.
- Validate configuration binding and provide safe defaults without hiding misconfiguration.
