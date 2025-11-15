"""
py_module.docgen

Small documentation generator that produces a Markdown README from:
- `analysis` (from code_analyzer.analyze_path)
- `ccg` (from ccg_builder.build_ccg)

Exports:
- generate_markdown(analysis, ccg) -> str
- build_and_write(analysis, ccg, out_path="/tmp/auto_README.md") -> dict
"""
from pathlib import Path
import datetime
import json
from typing import Dict, List

def _short(x, n=300):
    s = json.dumps(x) if not isinstance(x, str) else x
    return (s[:n] + "...") if len(s) > n else s

def _group_nodes_by_module(nodes: List[str]) -> Dict[str, List[str]]:
    groups = {}
    for n in nodes:
        if "." in n:
            mod, name = n.rsplit(".", 1)
        else:
            mod, name = "<root>", n
        groups.setdefault(mod, []).append(name)
    # sort names
    for k in groups:
        groups[k] = sorted(groups[k])
    return dict(sorted(groups.items()))

def _summarize_files(analysis):
    files = analysis.get("files", [])
    # produce a simple table-like list of the most important entries (first 40)
    out_lines = []
    for f in files[:120]:
        p = f.get("path") if isinstance(f, dict) else str(f)
        ext = f.get("ext","") if isinstance(f, dict) else Path(p).suffix
        todos = f.get("todos", []) if isinstance(f, dict) else []
        out_lines.append(f"| `{p}` | `{ext}` | {len(todos)} TODOs |")
    return out_lines

def generate_markdown(analysis: Dict, ccg: Dict) -> str:
    """
    Create a clear, logically ordered markdown README string.
    Sections:
      - Title & Generated meta
      - Project Overview
      - Quick stats
      - Installation
      - Usage
      - API Reference (module -> symbols)
      - Notes & TODOs
    """
    now = datetime.datetime.utcnow().isoformat() + "Z"
    lines = []
    # Header
    lines.append(f"# Auto-generated Project README\n")
    lines.append(f"_Generated: {now}_\n")

    # Overview
    lines.append("## Project overview\n")
    path = analysis.get("path", ".")
    lines.append(f"- Root path: `{path}`")
    lines.append(f"- Files analyzed: **{len(analysis.get('files',[]))}**")
    lines.append("")

    # Quick stats
    lines.append("## Quick stats\n")
    lines.append(f"- TODO count (found): **{analysis.get('summary',{}).get('todo_count', '?')}**")
    lines.append(f"- Python defs discovered (approx): **{analysis.get('summary',{}).get('python_defs', '?')}**")
    lines.append("")

    # Example files (short)
    lines.append("### Sample files scanned (first 120 rows)\n")
    lines.append("| path | ext | todo_count |")
    lines.append("|---|---:|---:|")
    sample = _summarize_files(analysis)
    if sample:
        lines.extend(sample)
    else:
        lines.append("- (no files listed)")

    lines.append("\n")

    # Installation
    lines.append("## Installation\n")
    lines.append("Steps to get the repo running locally (example):\n")
    lines.append("```bash")
    lines.append("python -m venv env")
    lines.append("source env/bin/activate   # or .\\env\\Scripts\\activate on Windows")
    lines.append("pip install -r requirements.txt   # if exists")
    lines.append("```")
    lines.append("")

    # Usage
    lines.append("## Usage\n")
    lines.append("Basic usage examples and quick commands:\n")
    lines.append("- Run tests: `pytest -q`")
    lines.append("- Run the local analysis helper (generates README):")
    lines.append("```bash")
    lines.append("python -c \"from py_module import code_analyzer as ca; print(ca.analyze_path('.'))\"")
    lines.append("```")
    lines.append("")

    # API Reference (derive from ccg)
    lines.append("## API Reference (auto-extracted)\n")
    nodes = ccg.get("nodes", []) if isinstance(ccg, dict) else []
    edges = ccg.get("edges", []) if isinstance(ccg, dict) else []

    if not nodes:
        lines.append("_No API symbols found in CCG._\n")
    else:
        grouped = _group_nodes_by_module(nodes)
        lines.append("This section lists modules and the top-level symbols (functions/classes) found.\n")
        for mod, syms in grouped.items():
            lines.append(f"### Module: `{mod}`\n")
            for s in syms:
                lines.append(f"- `{s}`")
            lines.append("")  # blank line

    # Relationship examples (callers/callees)
    lines.append("### Example relationships (callers/callees)\n")
    # pick a few example targets if available
    sample_targets = []
    for n in nodes[:10]:
        sample_targets.append(n.split(".")[-1])
    sample_targets = list(dict.fromkeys(sample_targets))[:5]
    if sample_targets:
        for t in sample_targets:
            callers = [e["src"] for e in edges if e.get("type")=="call" and (e.get("tgt","").split(".")[-1]==t or e.get("tgt","")==t)]
            callees = [e["tgt"] for e in edges if e.get("type")=="call" and (e.get("src","").split(".")[-1]==t or e.get("src","")==t)]
            lines.append(f"- **{t}**")
            if callers:
                lines.append(f"  - callers ({len(callers)}): " + ", ".join(sorted(set(callers))[:10]))
            if callees:
                lines.append(f"  - callees ({len(callees)}): " + ", ".join(sorted(set(callees))[:10]))
            if not callers and not callees:
                lines.append("  - (no direct call relationships found)")
            lines.append("")
    else:
        lines.append("- (no examples available)\n")

    # Notes & TODOs
    lines.append("## Notes & TODOs\n")
    todos = []
    for f in analysis.get("files", [])[:500]:
        if isinstance(f, dict):
            for t in f.get("todos", []):
                todos.append((f.get("path","<unknown>"), _short(t, 140)))
    if todos:
        lines.append("| file | TODO excerpt |")
        lines.append("|---|---|")
        for p, t in todos[:80]:
            lines.append(f"| `{p}` | {t} |")
    else:
        lines.append("- No TODOs extracted.")

    # Footer
    lines.append("\n---\n")
    lines.append("_This README was generated automatically from a lightweight static analysis and a code-context graph._")
    return "\n".join(lines)

def build_and_write(analysis: Dict, ccg: Dict, out_path: str = "/tmp/auto_README.md") -> Dict:
    md = generate_markdown(analysis, ccg)
    p = Path(out_path)
    p.write_text(md, encoding="utf-8")
    return {"output_path": str(p), "written": True, "len": len(md)}
