# Local analysis scripts

All scripts use Python standard library only and make no network calls.

```bash
python scripts/analyze_project.py --root . --output engineering/context
```

Outputs `ENGINEERING_INTELLIGENCE.md`, `ENGINEERING_INTELLIGENCE.json`, and
`ARCHITECTURE_GRAPH.mmd`.

This is static triage, not a compiler, effective Maven/Gradle model resolver, runtime call graph,
SAST scanner, or memory profiler. Review findings manually. Use approved Maven/Gradle commands,
security tools, JFR, GC logs and heap dumps for deeper validation.
