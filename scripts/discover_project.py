#!/usr/bin/env python3
"""Read-only, best-effort Java/Spring project inventory. Uses Python stdlib only."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timezone

SKIP = {".git", ".idea", ".vscode", "target", "build", ".gradle", ".mvn/wrapper"}
MAX_FILES = 5000

def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def version_from(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.M)
        if match:
            return match.group(1).strip()
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--output", default="engineering/context")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    output = (root / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)

    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP for part in rel.parts):
            continue
        if len(files) >= MAX_FILES:
            break
        files.append(p)

    poms = [p for p in files if p.name == "pom.xml"]
    gradles = [p for p in files if p.name in {"build.gradle", "build.gradle.kts"}]
    java_files = [p for p in files if p.suffix == ".java"]
    boot_versions, java_versions = [], []
    build_modules = []

    for pom in poms:
        content = read(pom)
        boot = version_from([
            r"<spring-boot\.version>\s*([^<]+)",
            r"<version>\s*(\d+\.\d+(?:\.\d+)?[^<]*)\s*</version>.*?<artifactId>\s*spring-boot-starter-parent\s*</artifactId>",
            r"<version>\s*([^<]+)\s*</version>.*?<artifactId>\s*spring-boot-dependencies\s*</artifactId>"
        ], content)
        java = version_from([
            r"<java\.version>\s*([^<]+)",
            r"<maven\.compiler\.(?:release|source)>\s*([^<]+)",
            r"<release>\s*([^<]+)"
        ], content)
        if boot: boot_versions.append({"file": str(pom.relative_to(root)), "version": boot})
        if java: java_versions.append({"file": str(pom.relative_to(root)), "version": java})
        build_modules.append(str(pom.relative_to(root)))

    for gradle in gradles:
        content = read(gradle)
        boot = version_from([r"org\.springframework\.boot['\"]?\s+version\s+['\"]([^'\"]+)"],
                            content)
        java = version_from([r"(?:JavaLanguageVersion\.of|VERSION_)(?:\()?\s*['\"]?(\d+)"],
                            content)
        if boot: boot_versions.append({"file": str(gradle.relative_to(root)), "version": boot})
        if java: java_versions.append({"file": str(gradle.relative_to(root)), "version": java})
        build_modules.append(str(gradle.relative_to(root)))

    for marker in [".java-version", ".sdkmanrc"]:
        p = root / marker
        if p.exists():
            content = read(p)
            val = version_from([r"(?:java=)?\s*([0-9]+(?:\.[0-9]+)*(?:[-+.\w]*)?)"], content)
            if val: java_versions.append({"file": marker, "version": val})

    top_packages = sorted({str(p.relative_to(root).parent) for p in java_files})
    dependency_names = set()
    for p in poms + gradles:
        text = read(p)
        for token in re.findall(r"(?:spring-boot-starter-[\w-]+|spring-boot-starter|spring-kafka|spring-rabbit|spring-jdbc|spring-data-[\w-]+|hibernate-core|testcontainers|junit-jupiter|mockito-core)", text, re.I):
            dependency_names.add(token)

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "discovery_mode": "read-only; best effort; no network; no build execution",
        "files_scanned": len(files),
        "build_files": build_modules,
        "java_version_evidence": java_versions,
        "spring_boot_version_evidence": boot_versions,
        "java_source_file_count": len(java_files),
        "top_java_package_paths": top_packages[:250],
        "recognized_dependency_tokens": sorted(dependency_names),
        "warnings": [
            "Version evidence may conflict or be inherited from parent/build logic.",
            "Effective Maven/Gradle models are not resolved; inspect parent POMs, profiles, properties and toolchains.",
            "Do not treat this inventory as a complete dependency or architecture graph.",
            "Configuration files were not parsed for secrets; do not add secret values to generated reports."
        ]
    }
    out = output / "PROJECT_DISCOVERY.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"Build files: {len(build_modules)} | Java sources: {len(java_files)}")
    print(f"Java version evidence: {java_versions or 'not detected'}")
    print(f"Spring Boot version evidence: {boot_versions or 'not detected'}")

if __name__ == "__main__":
    main()
