#!/usr/bin/env python3
"""Read-only repository inventory and static triage. Python stdlib only; no network/build execution."""
from __future__ import annotations
import argparse, collections, json, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SKIP = {".git", ".idea", ".vscode", "target", "build", ".gradle", "node_modules", ".venv", "venv", "__pycache__"}
MAX_FILES, MAX_BYTES = 12000, 2_000_000

def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace") if p.stat().st_size <= MAX_BYTES else ""
    except OSError:
        return ""

def local(tag): return tag.rsplit("}", 1)[-1]
def child(node, name):
    for x in list(node):
        if local(x.tag) == name and x.text: return x.text.strip()
    return None

def collect(root):
    out = []
    for p in root.rglob("*"):
        if p.is_file() and not any(x in SKIP for x in p.parts):
            out.append(p)
            if len(out) >= MAX_FILES: break
    return out

def pom_info(p, root):
    try: doc = ET.fromstring(read(p))
    except ET.ParseError: return {"path": str(p.relative_to(root)), "parse_error": True, "modules": [], "dependencies": []}
    props, modules, deps = {}, [], []
    for el in doc.iter():
        tag = local(el.tag)
        if tag == "properties":
            for x in list(el):
                if x.text: props[local(x.tag)] = x.text.strip()
        elif tag == "module" and el.text:
            modules.append(el.text.strip())
        elif tag == "dependency":
            g, a, v = child(el, "groupId"), child(el, "artifactId"), child(el, "version")
            if g or a: deps.append({"group": g, "artifact": a, "version": v})
    parent = None
    for el in list(doc):
        if local(el.tag) == "parent":
            parent = {"group": child(el,"groupId"), "artifact": child(el,"artifactId"), "version": child(el,"version")}
    boot = props.get("spring-boot.version")
    if parent and parent.get("artifact") == "spring-boot-starter-parent": boot = parent.get("version") or boot
    for d in deps:
        if d["artifact"] == "spring-boot-dependencies": boot = d["version"] or boot
    java = props.get("java.version") or props.get("maven.compiler.release") or props.get("maven.compiler.source")
    return {"path": str(p.relative_to(root)), "artifact_id": child(doc,"artifactId"),
            "packaging": child(doc,"packaging"), "parent": parent, "modules": modules,
            "java_version": java, "spring_boot_version": boot, "dependencies": deps}

def gradle_info(p, root):
    s = read(p)
    b = re.search(r"org\.springframework\.boot['\"]?\s+version\s+['\"]([^'\"]+)", s)
    j = re.search(r"(?:JavaLanguageVersion\.of|VERSION_)\s*\(?\s*['\"]?(\d+)", s)
    return {"path": str(p.relative_to(root)), "spring_boot_version": b.group(1) if b else None,
            "java_version": j.group(1) if j else None}

def analyze_java(java_files, root):
    packages, imports, edges, import_counts = collections.defaultdict(list), collections.Counter(), collections.Counter(), collections.Counter()
    source_records = []
    for p in java_files:
        s = read(p); rel = str(p.relative_to(root))
        m = re.search(r"^\s*package\s+([\w.]+)\s*;", s, re.M); pkg = m.group(1) if m else "(default)"
        packages[pkg].append(rel)
        imps = re.findall(r"^\s*import\s+(?:static\s+)?([\w.]+)\s*;", s, re.M)
        imports.update(imps)
        for imp in imps:
            target = imp.rsplit(".", 1)[0]
            if target != pkg and target.startswith(pkg.split(".")[0]): edges[(pkg,target)] += 1
        source_records.append({"path": rel, "package": pkg, "imports": imps, "lines": s.count("\n")+1})
    known = set(packages)
    graph = [{"from": a, "to": b, "imports": n} for (a,b),n in edges.items() if b in known]
    return {"java_file_count":len(java_files), "packages":dict(sorted(packages.items())),
            "package_dependency_edges":graph, "top_imports":imports.most_common(40),
            "source_files":source_records}

def static_findings(java_files, root):
    rules = [
      ("threadlocal",r"\bThreadLocal\b","ThreadLocal","Check remove() in finally and pooled-thread reuse."),
      ("mutable_static",r"\bstatic\s+(?!final\b)[\w<>, ?\[\].]+\s+\w+\s*(?:=|;)","Potential mutable static state","Review concurrency and classloader lifetime."),
      ("async",r"@Async\b","@Async usage","Review bounded executor, exceptions, context propagation and shutdown."),
      ("scheduled",r"@Scheduled\b","@Scheduled usage","Review overlap, multi-replica behavior, idempotency and shutdown."),
      ("retry",r"@Retryable\b|\bRetryTemplate\b","Retry usage","Review retry bounds, jitter, idempotency and retry storms."),
      ("process",r"Runtime\.getRuntime\(\)\.exec|new\s+ProcessBuilder","Process execution","Review input validation, permissions and process cleanup."),
      ("deserialization",r"ObjectInputStream","Native Java deserialization","Review trust boundary; never deserialize untrusted data."),
      ("random",r"\bnew\s+Random\s*\(","java.util.Random","If used for security tokens, use SecureRandom."),
      ("printstack",r"printStackTrace\s*\(","printStackTrace","Use structured logging; avoid sensitive data.")
    ]
    out=[]
    for p in java_files:
        s=read(p); rel=str(p.relative_to(root))
        for key,pat,title,advice in rules:
            for m in re.finditer(pat,s):
                out.append({"rule":key,"file":rel,"line":s.count("\n",0,m.start())+1,"title":title,"guidance":advice})
    return out

def duplicate_candidates(java_files, root):
    seen, result = {}, []
    for p in java_files:
        lines=[re.sub(r"\s+"," ",x.strip()) for x in read(p).splitlines()
               if x.strip() and not x.strip().startswith(("//","*","/*"))]
        for size in (8,12):
            for i in range(max(0,len(lines)-size+1)):
                block="\n".join(lines[i:i+size])
                if len(block)<100: continue
                key=__import__("hashlib").sha256(block.encode()).hexdigest()
                rel=str(p.relative_to(root))
                if key in seen and seen[key] != rel:
                    result.append({"file_a":seen[key],"file_b":rel,"lines":size,
                                   "note":"Exact normalized text candidate; manually verify semantics."})
                else: seen[key]=rel
    return result[:200]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",default="."); ap.add_argument("--output",default="engineering/context")
    args=ap.parse_args(); root=Path(args.root).resolve(); out=(root/args.output).resolve(); out.mkdir(parents=True,exist_ok=True)
    fs=collect(root); java=[p for p in fs if p.suffix==".java"]
    poms=[pom_info(p,root) for p in fs if p.name=="pom.xml"]
    grads=[gradle_info(p,root) for p in fs if p.name in {"build.gradle","build.gradle.kts"}]
    jinfo=analyze_java(java,root); findings=static_findings(java,root); dups=duplicate_candidates(java,root)
    jvers=[{"file":x["path"],"version":x.get("java_version")} for x in poms+grads if x.get("java_version")]
    bvers=[{"file":x["path"],"version":x.get("spring_boot_version")} for x in poms+grads if x.get("spring_boot_version")]
    modules=[{"declared_in":x["path"],"module":m} for x in poms for m in x.get("modules",[])]
    deps=[{"declared_in":x["path"],**d} for x in poms for d in x.get("dependencies",[])]
    configs=[str(p.relative_to(root)) for p in fs if p.name in {"application.yml","application.yaml","application.properties","Dockerfile","Chart.yaml"}
             or (p.suffix in {".yaml",".yml"} and any(k in str(p).lower() for k in ("k8s","kubernetes","helm","deploy")))]
    report={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"root":str(root),
      "mode":"read-only static analysis; stdlib only; no network or build execution",
      "technology":{"java_version_evidence":jvers,"spring_boot_version_evidence":bvers,
                    "build_files":[str(p.relative_to(root)) for p in fs if p.name in {"pom.xml","build.gradle","build.gradle.kts"}]},
      "architecture":{"maven_projects":poms,"gradle_builds":grads,"declared_maven_modules":modules,
                      "declared_maven_dependencies":deps,"configuration_files":configs,
                      "java_package_dependency_edges":jinfo["package_dependency_edges"]},
      "code":jinfo,"quality_findings":findings,"duplicate_candidates":dups,
      "limitations":["Static heuristics can produce false positives/negatives.",
        "Maven effective models, profiles, inherited properties and dependency mediation are not resolved.",
        "Gradle scripts are inspected heuristically; no Gradle model is evaluated.",
        "Package edges are approximations, not runtime call graphs.",
        "No runtime profiling, heap diagnosis, SAST, build, or tests are performed."]}
    (out/"ENGINEERING_INTELLIGENCE.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    md=["# Engineering Intelligence Report","",f"Generated: {report['generated_at_utc']}","",
      "## Technology evidence","",f"- Java: `{json.dumps(jvers)}`",f"- Spring Boot: `{json.dumps(bvers)}`",
      f"- Java source files: {len(java)}",f"- Maven modules declared: {len(modules)}",
      f"- Maven dependency declarations: {len(deps)}",f"- Package dependency edges: {len(jinfo['package_dependency_edges'])}",
      f"- Static review indicators: {len(findings)}",f"- Duplicate text candidates: {len(dups)}","",
      "## Static review indicators",""]
    md += [f"- `{x['file']}:{x['line']}` **{x['title']}** — {x['guidance']}" for x in findings[:150]]
    md += ["","## Limitations",""]+["- "+x for x in report["limitations"]]
    (out/"ENGINEERING_INTELLIGENCE.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    graph=["flowchart LR"]+[f'  "{e["from"]}" -->|{e["imports"]} imports| "{e["to"]}"' for e in jinfo["package_dependency_edges"]]
    (out/"ARCHITECTURE_GRAPH.mmd").write_text("\n".join(graph)+"\n",encoding="utf-8")
    print(f"Reports written to {out}; Java files={len(java)}, findings={len(findings)}")
if __name__=="__main__": main()
