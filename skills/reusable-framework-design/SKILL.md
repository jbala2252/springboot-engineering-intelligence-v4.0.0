---
name: reusable-framework-design
description: Designs configurable shared capabilities across Spring Boot modules.
---
# Reusable Framework Design
Find repeated business-neutral capabilities across at least two real modules. Separate stable core
behavior from variable policies, configuration and extension points. Compare shared library, Spring Boot
starter, internal service, template and local implementation. Consider dependency direction, optional
integrations, auto-configuration, version alignment, semantic versioning, security, observability,
adoption, migration and ownership. Do not create a framework without a stable contract and proven reuse.
