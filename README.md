# Spring Boot Engineering Intelligence Kit

An internal, MCP-free GitHub Copilot customization package for Spring Boot repositories.
Designed for VS Code and IntelliJ IDEA, with shared engineering skills and IDE-specific
Copilot agents where supported.

## Principles

- No external MCP server, hosted service, or external AI dependency is configured.
- Detect the project's actual Java, Spring Boot, Maven/Gradle, and dependency versions.
- Treat source code and executable build configuration as evidence; documentation may be stale.
- Discover before designing; plan before substantial edits; validate before completion.
- Prefer adaptable, reusable, secure, observable, maintainable designs without needless abstraction.
- Never claim a command or test passed unless it was actually run and its result inspected.

## v4 capabilities

- Configurable engineering governance rules and advisory reports.
- Pull request review checklist and technical-debt register.
- Evidence-based engineering maturity assessment.
- Approved engineering pattern catalog and governance skill.
- No automatic policy changes or blocking CI enforcement by default.

Run `python scripts/governance_check.py --root . --standards config/engineering-standards.json`.

## v3 capabilities

- Cross-repository comparison of explicitly selected Spring Boot repositories.
- Java/Spring Boot version evidence and shared dependency inventory.
- Cross-module standardization and reusable-framework opportunity analysis.
- Repository manifest support for repeatable organization-wide scans.

Run:

```bash
python scripts/cross_module_intelligence.py --manifest engineering-repositories.json --output engineering/cross-module
```

See `docs/CROSS-MODULE-INTELLIGENCE.md` for setup and limitations.

## v2 capabilities

- Architecture inventory: Maven modules/dependencies, Java package relationships, configuration inventory.
- Code-quality triage: static review indicators and exact-text duplication candidates.
- Reliability triage: targeted prompts for ThreadLocal, schedulers, async work and retry behavior.
- Reusable framework design: evidence-based library/starter/service/template decisions.
- Engineering knowledge: ADR, lessons-learned and validated pattern catalog.
- Unified Markdown, JSON and Mermaid reports.

Run:

```bash
python scripts/analyze_project.py --root . --output engineering/context
```

Static findings are approximations, not proof of defects or runtime behavior.

## Package layout

- `skills/`: portable, on-demand workflows.
- `com.github.copilot/agents/`: Copilot-specific agent profiles.
- `templates/`: repository-level instruction and context templates.
- `scripts/`: local Python discovery, single-repository analysis and cross-repository intelligence.
- `docs/`: installation and operating guidance.

## Install

### VS Code

1. Open Copilot Chat and open the Agent Customizations editor.
2. Install this plugin from the approved internal Git repository or local plugin folder,
   if Agent Plugins are enabled by your organization.
3. Ensure the Copilot agent harness is selected.
4. Open a Spring Boot repository and run the `project-discovery` skill or ask the
   Engineering Orchestrator to inspect the repository.
5. If plugin installation is restricted, copy `templates/.github/` into the target repo
   and use the skill and agent files from the approved customization location.

### IntelliJ IDEA

1. Update the GitHub Copilot plugin to an organization-approved version.
2. Open Copilot Chat > settings/customizations.
3. Add the shared instruction file from `templates/.github/copilot-instructions.md`
   as workspace instructions, where supported.
4. Add/import the skills from `skills/` through the Agent Customizations editor, where
   Agent Skills are enabled for your IDE version.
5. Add the relevant agent profiles from `com.github.copilot/agents/` through the
   customizations editor, where custom agents are supported.
6. Verify the capabilities visible in your installed IntelliJ/Copilot versions.

**Compatibility note:** GitHub's plugin bundle installation surfaces are not identical
across IDEs. This package shares portable skills and instructions, while agent profiles
are Copilot-specific. IntelliJ may require importing individual customizations rather
than installing the whole plugin bundle. Check the organization's approved Copilot
version and feature policies.

## Project discovery

Run:

```bash
python scripts/discover_project.py --root . --output engineering/context
```

The script is read-only. It inspects build/configuration files and emits a best-effort
inventory. It does not download dependencies, invoke Maven/Gradle, or access the network.

## Recommended first request

"Use the Engineering Orchestrator. Discover this repository, inspect the actual
technology versions and module boundaries, compare existing architecture documentation
with source/build configuration, and produce a context report. Do not modify application
code."

## Security and governance

- Review scripts before execution and commit them through your organization's normal process.
- Run only approved local commands.
- Do not include secrets, credentials, production data, or private keys in generated context.
- Do not add MCP configuration. The package intentionally contains no `mcp.json`.
- Apply normal branch protection, code review, SAST, dependency scanning, and CI policies.
