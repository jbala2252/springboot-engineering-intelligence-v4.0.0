# v4 Engineering Governance

Run:
```bash
python scripts/governance_check.py --root /path/to/repository --standards config/engineering-standards.json --output engineering/governance
```
Outputs `GOVERNANCE_REPORT.md` and `GOVERNANCE_REPORT.json`.

Includes configurable advisory rules, PR review checklist, technical-debt register, maturity
assessment, approved-pattern catalog, and governance agent/skill.

Review findings with code owners. Promote patterns only after validation and approval.
Default checks are advisory; do not block CI until policy owners approve rules and false-positive
rates. This tool does not modify source code or organizational standards.
