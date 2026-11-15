---
name: cross-module-intelligence
description: Compares multiple Spring Boot repositories for dependency alignment, duplicated capabilities, architectural inconsistencies and shared-framework opportunities.
---
# Cross-Module Intelligence

1. Establish the repository set explicitly; do not scan parent directories or unrelated workspaces by assumption.
2. Run `scripts/cross_module_intelligence.py` against the selected roots or a reviewed manifest.
3. Inspect each repository's effective build configuration using approved Maven/Gradle commands when allowed.
4. Compare Java/Spring Boot baselines, dependency coordinates, plugin versions, test stacks, configuration conventions and deployment assumptions.
5. Investigate common dependencies for version alignment, ownership and security policy; differences are not automatically defects.
6. Search repeated implementations and validate semantic equivalence before proposing shared code.
7. Identify candidates for shared library, Spring Boot starter, platform service, template, or local implementation.
8. Assess adoption cost, migration path, versioning, backward compatibility, support ownership and operational risk.
9. Produce an evidence-backed opportunity backlog ranked by impact, confidence, effort and risk.

Never infer repository relationships from directory names alone. Do not copy source code between repositories or modify multiple repositories without explicit authorization.
