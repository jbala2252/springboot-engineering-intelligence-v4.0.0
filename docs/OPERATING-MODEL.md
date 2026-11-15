# Operating model

## Default request lifecycle

1. Classify task size and risk.
2. Discover relevant repository context.
3. Load relevant skills only.
4. Inspect existing code and tests.
5. Research from approved/local sources; state when external research is unavailable.
6. Produce options and a recommendation for substantial changes.
7. Obtain approval for high-impact work.
8. Implement in small coherent changes.
9. Run focused tests, build, and static checks as authorized.
10. Review security, compatibility, performance, and documentation.
11. Report exact changes, evidence, failed/unrun checks, and remaining risks.

## Risk tiers

- Low: localized typo, simple explanation, isolated low-risk fix. Keep workflow lightweight.
- Medium: single-module feature or refactor. Inspect relevant module, plan, test.
- High: cross-module, persistence, concurrency, security, dependency upgrade, public contract,
  deployment, or data migration. Full discovery, options, approval, rollout and rollback.

## Version detection precedence

Use build-tool effective configuration where available. Static discovery is evidence only:
Maven parent inheritance, profiles, properties, imported BOMs, Gradle plugins/toolchains,
and CI overrides can change the effective version. If declarations disagree, report all evidence
and ask for clarification or run approved build-tool help/effective-model commands.

## No MCP

This package intentionally does not include `mcp.json`, external tool endpoints, or external
service credentials. Local scripts use Python's standard library. Maven/Gradle commands are
invoked by the agent only when authorized and available.
