---
name: project-discovery
description: Discover repository structure and actual technology baseline before engineering work.
---

# Project Discovery

1. Inspect root files and module directories.
2. Read `pom.xml`, parent POMs, Maven wrapper properties, Gradle settings/build files,
   toolchain declarations, `.java-version`, and `.sdkmanrc` when present.
3. Identify Java and Spring Boot versions, build system, modules, plugins, dependencies,
   test frameworks, packaging, and deployment descriptors.
4. Inspect source packages and configuration to identify entry points, controllers,
   services, repositories, clients, schedulers, listeners, messaging, security, and persistence.
5. Compare existing context docs with current build/source evidence.
6. Run `python scripts/discover_project.py --root . --output engineering/context`
   if the script is available and execution is authorized.
7. Report conflicting declarations, missing evidence, and confidence.

Do not download dependencies or access network unless explicitly authorized. Never print secret values.

