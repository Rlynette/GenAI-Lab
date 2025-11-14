"""
py_module.docgen

Lightweight Markdown generator for project README from analysis + ccg.
"""
from pathlib import Path
import datetime
import json

def _safe_short(x, n=300):
    s = json.dumps(x) if not isinstance(x, str) else x
    return (s[:n] + "...") if len(s) > n else s

def generate_markdown(analysis, ccg):
    now = datetime.datetime.utcnow().isoformat() + "Z"
    lines = []
    lines.append(f"# Auto-generated Project README\n\n*Generated: {now}*\n")
    lines.append("## Project Overview\n")
    lines.append(f"- Root path: `{analysis.get('path','.')}`\n")
    lines.append(f"- Files scanned: {len(analysis.get('files', []))}\n\n")

    # Installation hints (best-effort)
    lines.append("## Installation\n")
    files = [f.get("path","") for f in analysis.get("files",[])]
    if any(p.endswith("requirements.txt") for p in files):
        lines.append("- Create a virtualenv and `pip install -r requirements.txt`\n")
    elif any(p.endswith("pyproject.toml") or p.endswith("setup.py") for p in files):
        lines.append("- Standard python packaging: see `pyproject.toml` / `setup.py`.\n")
    else:
        lines.append("- No explicit Python requirements detected. If the project is Python-based, install dependencies as needed.\n")
    lines.append("\n## Usage\n")
    lines.append("This repo ships JAC walkers (backend). Example HTTP endpoints you can call on a running local server:\n\n")
    lines.append("```bash\n# analyze repo\ncurl -X POST http://127.0.0.1:8000/walker/repo_analyze \\\n  -H \"Content-Type: application/json\" -H \"Authorization: Bearer <TOKEN>\" \\\n  --data-binary '{\"body\":{\"repo_path\":\"./\",\"depth\":1}}'\n```\n\n")

    lines.append("## API Reference (auto-extracted)\n")
    # List functions/classes from ccg
    funcs = [n for n in ccg.get("nodes",[]) if n.get("type") in ("function","method")]
    classes = [n for n in ccg.get("nodes",[]) if n.get("type") == "class"]
    if funcs:
        lines.append("### Functions / Methods\n")
        lines.append("| Name | Type | File |\n|---|---:|---|\n")
        for f in sorted(funcs, key=lambda x: x["id"]):
            lines.append(f"| `{f['id']}` | {f.get('type','')} | `{f.get('file','')}` |")
        lines.append("\n")
    if classes:
        lines.append("### Classes\n")
        lines.append("| Name | File |\n|---|---|\n")
        for c in sorted(classes, key=lambda x: x["id"]):
            lines.append(f"| `{c['id']}` | `{c.get('file','')}` |")
        lines.append("\n")

    lines.append("## Notes\n")
    lines.append("- This README was generated automatically from a lightweight static analysis.\n")
    lines.append("- Check generated `ccg` (nodes/edges) to produce diagrams or include as part of documentation.\n")

    return "\n".join(lines)

def build_and_write(analysis, ccg, out_path="/tmp/auto_README.md"):
    md = generate_markdown(analysis, ccg)
    Path(out_path).write_text(md, encoding="utf-8")
    return {"output_path": out_path, "written": True, "len": len(md)}
