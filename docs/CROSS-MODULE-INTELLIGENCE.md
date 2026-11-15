# Cross-module intelligence

## Define the repository set

Create a JSON manifest based on `templates/engineering/engineering-repositories.example.json`.
Use explicit paths to repositories you are authorized to inspect. Relative paths resolve from the
manifest file's directory.

## Run

```bash
python scripts/cross_module_intelligence.py \
  --manifest engineering-repositories.json \
  --output engineering/cross-module
```

Or:

```bash
python scripts/cross_module_intelligence.py \
  --roots ../module-a ../module-b ../module-c \
  --output engineering/cross-module
```

Outputs:
- `CROSS_MODULE_INTELLIGENCE.md`
- `CROSS_MODULE_INTELLIGENCE.json`

## What it compares

- Java and Spring Boot version evidence.
- Maven/Gradle build files and declared Maven modules.
- Dependency coordinates declared across repositories.
- Package inventories and selected source review indicators.
- Candidate repeated source blocks within each repository.

## What it does not prove

- Effective dependency convergence or transitive version conflicts.
- Semantic code duplication across repositories.
- Runtime call paths, memory leaks, security vulnerabilities or production behavior.
- That a common dependency or repeated pattern should become a shared platform component.

Use approved Maven/Gradle dependency reports, AST-aware tooling, security scanners and runtime
profiling to validate important conclusions. The tool is read-only and makes no network calls.
