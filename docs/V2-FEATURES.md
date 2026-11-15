# v2 capabilities

1. **Architecture intelligence:** inventories Maven module/dependency declarations, Java packages/imports,
   config/deployment files; emits JSON, Markdown and Mermaid.
2. **Code intelligence:** flags selected patterns (ThreadLocal, mutable static fields, @Async, @Scheduled,
   retries, process execution, native deserialization, Random, printStackTrace) and exact-text clone candidates.
3. **Reliability triage:** guides follow-up with JFR, GC logs, heap dumps, dominator trees, thread dumps,
   lifecycle inspection and load tests. Static scans do not prove leaks.
4. **Reusable framework design:** compares library, starter, internal service, template or local implementation.
5. **Engineering knowledge:** ADR, lessons-learned and validated pattern-catalog templates.
6. **Governance:** no MCP, no external service, no automatic application edits, no dependency upgrades,
   no network access, no runtime profiling or security scan from the analyzer.
