#!/usr/bin/env python3
"""
Cross-repository intelligence for multiple Java/Spring Boot modules.
Read-only, Python standard library only. No network, build execution, or source modification.

Usage:
  python scripts/cross_module_intelligence.py --roots /work/module-a /work/module-b
  python scripts/cross_module_intelligence.py --manifest engineering-repositories.json

Manifest format:
{
  "repositories": [
    {"name": "payments", "path": "../payments"},
    {"name": "reporting", "path": "../reporting"}
  ]
}
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SKIP = {".git", ".idea", ".vscode", "target", "build", ".gradle", "node_modules",
        ".venv", "venv", "__pycache__", ".terraform"}
MAX_FILES_PER_REPO = 15000
MAX_BYTES = 2_000_000
PATTERNS = {
    "ThreadLocal": r"\bThreadLocal\b",
    "Scheduled jobs": r"@Scheduled\b",
    "Async execution": r"@Async\b",
    "Retry mechanisms": r"@Retryable\b|\bRetryTemplate\b",
    "Native Java deserialization": r"\bObjectInputStream\b",
    "Process execution": r"Runtime\.getRuntime\(\)\.exec|new\s+ProcessBuilder",
    "printStackTrace": r"printStackTrace\s*\(",
    "Mutable static candidates": r"\bstatic\s+(?!final\b)[\w<>, ?\[\].]+\s+\w+\s*(?:=|;)"
}

def read(p: Path) -> str:
    try:
        if p.stat().st_size > MAX_BYTES:
            return ""
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""

def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]

def child(node, name):
    for item in list(node):
        if local(item.tag) == name and item.text:
            return item.text.strip()
    return None

def scan_files(repo: Path):
    found = []
    for p in repo.rglob("*"):
        if p.is_file() and not any(part in SKIP for part in p.parts):
            found.append(p)
            if len(found) >= MAX_FILES_PER_REPO:
                break
    return found

def parse_pom(path: Path, repo: Path):
    text = read(path)
    try:
        doc = ET.fromstring(text)
    except ET.ParseError:
        return {"file": str(path.relative_to(repo)), "parse_error": True,
                "dependencies": [], "modules": [], "java": None, "boot": None}
    props, deps, modules = {}, [], []
    for el in doc.iter():
        tag = local(el.tag)
        if tag == "properties":
            for x in list(el):
                if x.text:
                    props[local(x.tag)] = x.text.strip()
        elif tag == "module" and el.text:
            modules.append(el.text.strip())
        elif tag == "dependency":
            g, a, v = child(el, "groupId"), child(el, "artifactId"), child(el, "version")
            if g or a:
                deps.append({"group": g, "artifact": a, "version": v,
                             "coordinate": f"{g or '?' }:{a or '?'}"})
    parent = None
    for el in list(doc):
        if local(el.tag) == "parent":
            parent = {"artifact": child(el, "artifactId"), "version": child(el, "version")}
    boot = props.get("spring-boot.version")
    if parent and parent["artifact"] == "spring-boot-starter-parent":
        boot = parent["version"] or boot
    for dep in deps:
        if dep["group"] == "org.springframework.boot" and dep["artifact"] == "spring-boot-dependencies":
            boot = dep["version"] or boot
    java = props.get("java.version") or props.get("maven.compiler.release") or props.get("maven.compiler.source")
    return {"file": str(path.relative_to(repo)), "artifact": child(doc, "artifactId"),
            "parent": parent, "dependencies": deps, "modules": modules,
            "java": java, "boot": boot}

def parse_gradle(path: Path, repo: Path):
    s = read(path)
    b = re.search(r"org\.springframework\.boot['\"]?\s+version\s+['\"]([^'\"]+)", s)
    j = re.search(r"(?:JavaLanguageVersion\.of|VERSION_)\s*\(?\s*['\"]?(\d+)", s)
    deps = []
    for g, a, v in re.findall(r"""(['"])([\w.-]+):([\w.-]+):([\w.+-]+)\1""", s):
        deps.append({"group": a, "artifact": v, "version": None})
    return {"file": str(path.relative_to(repo)), "boot": b.group(1) if b else None,
            "java": j.group(1) if j else None, "dependencies": deps, "modules": []}

def normalized_block_hashes(java_files, repo):
    seen = {}
    for p in java_files:
        lines = [re.sub(r"\s+", " ", line.strip()) for line in read(p).splitlines()
                 if line.strip() and not line.strip().startswith(("//", "*", "/*"))]
        rel = str(p.relative_to(repo))
        for size in (10, 16):
            for i in range(max(0, len(lines) - size + 1)):
                block = "\n".join(lines[i:i+size])
                if len(block) < 120:
                    continue
                digest = hashlib.sha256(block.encode("utf-8")).hexdigest()
                seen.setdefault(digest, []).append({"file": rel, "start_line_approx": i + 1,
                                                    "block_lines": size})
    return {k: v for k, v in seen.items() if len({x["file"] for x in v}) > 1}

def scan_repo(name: str, repo: Path):
    files = scan_files(repo)
    java_files = [p for p in files if p.suffix == ".java"]
    poms = [parse_pom(p, repo) for p in files if p.name == "pom.xml"]
    grads = [parse_gradle(p, repo) for p in files if p.name in {"build.gradle", "build.gradle.kts"}]
    java_evidence = [{"file": x["file"], "version": x["java"]} for x in poms + grads if x.get("java")]
    boot_evidence = [{"file": x["file"], "version": x["boot"]} for x in poms + grads if x.get("boot")]
    deps = []
    for build in poms + grads:
        for dep in build.get("dependencies", []):
            if dep.get("group") and dep.get("artifact"):
                deps.append({**dep, "build_file": build["file"]})
    package_counts = collections.Counter()
    patterns = collections.defaultdict(list)
    for p in java_files:
        s = read(p)
        m = re.search(r"^\s*package\s+([\w.]+)\s*;", s, re.M)
        package_counts[m.group(1) if m else "(default)"] += 1
        rel = str(p.relative_to(repo))
        for label, regex in PATTERNS.items():
            for match in re.finditer(regex, s):
                patterns[label].append({"file": rel, "line": s.count("\n", 0, match.start()) + 1})
    return {
        "name": name, "path": str(repo), "exists": repo.exists(),
        "files_scanned": len(files), "java_file_count": len(java_files),
        "build_files": [str(p.relative_to(repo)) for p in files
                        if p.name in {"pom.xml", "build.gradle", "build.gradle.kts"}],
        "java_version_evidence": java_evidence,
        "spring_boot_version_evidence": boot_evidence,
        "maven_projects": poms, "gradle_projects": grads,
        "dependencies": deps, "declared_modules": [
            {"build_file": b["file"], "module": m} for b in poms + grads for m in b.get("modules", [])],
        "package_counts": dict(package_counts),
        "review_indicators": dict(patterns),
        "duplicate_candidates": normalized_block_hashes(java_files, repo),
        "limitations": [
            "Static declarations are not effective Maven/Gradle models.",
            "Dependency versions may be inherited, property-substituted, profile-controlled, or mediated.",
            "Source pattern matches are review indicators, not defects.",
            "Text-block matches are candidates, not semantic clone detection."
        ]
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--roots", nargs="*", default=[])
    ap.add_argument("--manifest")
    ap.add_argument("--output", default="engineering/cross-module")
    args = ap.parse_args()
    entries = []
    if args.manifest:
        manifest_path = Path(args.manifest).resolve()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in data.get("repositories", []):
            path = Path(item["path"])
            if not path.is_absolute():
                path = (manifest_path.parent / path).resolve()
            entries.append((item.get("name", path.name), path))
    else:
        entries = [(Path(x).name, Path(x).resolve()) for x in args.roots]
    if not entries:
        ap.error("Provide --roots PATH [PATH ...] or --manifest FILE")
    results = [scan_repo(name, path) for name, path in entries]
    # Aggregate dependency presence and declared-version evidence across repos.
    dep_map = collections.defaultdict(list)
    boot_map, java_map = collections.defaultdict(list), collections.defaultdict(list)
    for r in results:
        for d in r["dependencies"]:
            dep_map[d["coordinate"]].append({"repository": r["name"], "version_declared": d.get("version"),
                                               "build_file": d["build_file"]})
        for item in r["spring_boot_version_evidence"]:
            boot_map[str(item["version"])].append({"repository": r["name"], "file": item["file"]})
        for item in r["java_version_evidence"]:
            java_map[str(item["version"])].append({"repository": r["name"], "file": item["file"]})
    shared = [{"coordinate": k, "repositories": v} for k, v in dep_map.items() if len({x["repository"] for x in v}) > 1]
    cross_repo_duplicates = collections.defaultdict(list)
    for r in results:
        for digest, locations in r["duplicate_candidates"].items():
            for loc in locations:
                cross_repo_duplicates[digest].append({"repository": r["name"], **loc})
    # Cross-repository exact block scan: compare hashes are computed within each repo above;
    # re-scan files only where common patterns indicate potential reuse. We avoid pretending
    # that within-repo duplicate hashes are cross-repo proof.
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "read-only static cross-repository inventory; no network or build execution",
        "repository_count": len(results), "repositories": results,
        "shared_dependency_coordinates": shared,
        "spring_boot_version_distribution": dict(boot_map),
        "java_version_distribution": dict(java_map),
        "notes": [
            "A shared dependency coordinate does not imply version alignment or a reason to centralize it.",
            "Version differences are evidence for review, not automatically conflicts.",
            "To prove effective dependency convergence, run approved Maven/Gradle dependency reports.",
            "Cross-repository semantic code duplication requires AST/semantic tooling or manual review."
        ]
    }
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "CROSS_MODULE_INTELLIGENCE.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    md = ["# Cross-Module Engineering Intelligence", "",
          f"Generated: {report['generated_at_utc']}", f"Repositories scanned: {len(results)}", "",
          "## Repository overview", "",
          "| Repository | Java files | Java evidence | Spring Boot evidence | Build files |",
          "|---|---:|---|---|---:|"]
    for r in results:
        md.append(f"| {r['name']} | {r['java_file_count']} | {r['java_version_evidence']} | "
                  f"{r['spring_boot_version_evidence']} | {len(r['build_files'])} |")
    md += ["", "## Dependencies declared in multiple repositories", ""]
    for d in shared:
        md.append(f"- **{d['coordinate']}**: " + ", ".join(
            f"{x['repository']} (declared version: {x['version_declared'] or 'managed/unspecified'})"
            for x in d["repositories"]))
    if not shared: md.append("- No shared coordinates detected in the inspected declarations.")
    md += ["", "## Version distributions", "",
           "### Java", "", *[f"- `{v}`: {', '.join(x['repository'] for x in repos)}"
                              for v, repos in java_map.items()],
           "", "### Spring Boot", "", *[f"- `{v}`: {', '.join(x['repository'] for x in repos)}"
                                         for v, repos in boot_map.items()],
           "", "## Review guidance", "",
           "- Investigate version differences against support policy and actual effective build models.",
           "- Check shared dependencies for compatible versions, ownership and vulnerability status.",
           "- Promote repeated patterns only after verifying common behavior and stable contracts.",
           "- Do not infer memory leaks from static indicators; collect runtime evidence.",
           "", "## Limitations", ""] + [f"- {x}" for x in report["notes"]]
    (out / "CROSS_MODULE_INTELLIGENCE.md").write_text("\\n".join(md) + "\\n", encoding="utf-8")
    print(f"Scanned {len(results)} repositories. Reports written to {out}")

if __name__ == "__main__":
    main()
