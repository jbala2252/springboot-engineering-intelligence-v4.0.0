#!/usr/bin/env python3
"""Read-only advisory engineering governance checks; Python standard library only."""
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
SKIP={".git",".idea",".vscode","target","build",".gradle","node_modules",".venv","venv","__pycache__"}
def read(p):
    try: return p.read_text(encoding="utf-8",errors="replace") if p.stat().st_size<2_000_000 else ""
    except OSError: return ""
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="."); ap.add_argument("--standards",default="config/engineering-standards.json")
    ap.add_argument("--output",default="engineering/governance"); a=ap.parse_args()
    root=Path(a.root).resolve(); sp=Path(a.standards).resolve(); cfg=json.loads(sp.read_text(encoding="utf-8"))
    excludes=SKIP|set(cfg.get("policy",{}).get("exclude_paths",[])); files=[]
    for p in root.rglob("*"):
        if p.is_file() and not any(x in excludes for x in p.parts):
            files.append(p)
            if len(files)>=20000: break
    findings=[]
    for rule in cfg.get("rules",[]):
        try: rx=re.compile(rule["pattern"])
        except (KeyError,re.error) as e:
            findings.append({"rule_id":rule.get("id","INVALID"),"severity":"high","title":"Invalid rule","file":str(sp),"line":1,"guidance":str(e)}); continue
        exts=set(rule.get("file_extensions",[]))
        for p in files:
            if exts and p.suffix not in exts: continue
            text=read(p)
            for m in rx.finditer(text):
                findings.append({"rule_id":rule.get("id"),"severity":rule.get("severity","low"),
                    "title":rule.get("title"),"file":str(p.relative_to(root)),
                    "line":text.count("\\n",0,m.start())+1,"guidance":rule.get("guidance","Review match.")})
    counts={x:sum(f["severity"]==x for f in findings) for x in ("high","medium","low")}
    report={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"root":str(root),
      "mode":cfg.get("policy",{}).get("mode","advisory"),"files_scanned":len(files),
      "finding_counts":counts,"findings":findings,
      "limitations":["Regex checks can have false positives/negatives.","Not SAST, semantic analysis, compilation, dependency scanning or runtime verification.","Review matches before remediation or CI enforcement."]}
    out=Path(a.output); out=out if out.is_absolute() else root/out; out.mkdir(parents=True,exist_ok=True)
    (out/"GOVERNANCE_REPORT.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    lines=["# Engineering Governance Report","",f"Generated: {report['generated_at_utc']}",f"Mode: {report['mode']}",f"Files scanned: {len(files)}","",
      f"- High: {counts['high']}",f"- Medium: {counts['medium']}",f"- Low: {counts['low']}",""]
    lines += [f"- **[{f['severity'].upper()}] {f['rule_id']}** `{f['file']}:{f['line']}` {f['title']} — {f['guidance']}" for f in findings]
    lines += ["","## Limitations",""]+["- "+x for x in report["limitations"]]
    (out/"GOVERNANCE_REPORT.md").write_text("\\n".join(lines)+"\\n",encoding="utf-8")
    print(f"Scanned {len(files)} files; findings={len(findings)}; output={out}")
if __name__=="__main__": main()
