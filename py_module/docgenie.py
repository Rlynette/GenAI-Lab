"""Simple DocGenie: convert analysis data + CCG into a human-readable markdown doc."""
from pathlib import Path
from typing import Optional, Dict, Any
from . import code_analyzer as ca

TEMPLATE_HEADER = "# Project documentation (auto-generated)\n\n"

def _table_of_defs(ccg: Dict[str, Any]) -> str:
    lines = []
    lines.append("## API Reference (extracted)\n")
    lines.append("| Type | Name | Module | Notes |\n")
    lines.append("|---|---|---|---|\n")
    for nid, nd in sorted(ccg.get("nodes", {}).items()):
        t = nd.get("type", "")
        name = nd.get("name", "") or nid
        module = nd.get("module", "") or ""
        notes = ""
        if t.startswith("unresolved"):
            notes = "unresolved (external or dynamic call)"
        lines.append(f"| {t} | `{name}` | `{module}` | {notes} |\n")
    return "\n".join(lines)

def generate_markdown(repo_path: str, ccg: Optional[Dict] = None, analysis: Optional[Dict] = None, output_path: Optional[str] = None) -> str:
    repo_path_p = Path(repo_path) if repo_path else Path(".")
    analysis = analysis or ca.analyze_path(str(repo_path_p))
    ccg = ccg or ca.analyze_ccg(str(repo_path_p))

    parts = []
    parts.append(TEMPLATE_HEADER)
    parts.append(f"**Repo path:** `{str(repo_path_p)}`\n\n")
    parts.append("## Project overview\n")
    parts.append("This document was generated from a static analysis run. It includes a summary of files, TODOs, and an extracted Code Context Graph (CCG) describing functions, classes and call relationships.\n\n")
    parts.append("## Installation\n")
    parts.append("```bash\n# pip install -r requirements.txt\n```\n\n")
    parts.append("## Usage\n")
    parts.append("Describe how to run the project (add examples here).\n\n")
    parts.append("## Analysis summary\n")
    parts.append(f"- Files analyzed: **{len(analysis.get('files', []))}**\n")
    parts.append(f"- TODOs found: **{analysis.get('summary', {}).get('todo_count', 0)}**\n")
    parts.append(f"- Python defs found: **{analysis.get('summary', {}).get('python_defs', 0)}**\n\n")
    parts.append("### TODOs (sample)\n")
    sample_todos = []
    for f in analysis.get("files", [])[:50]:
        for t in f.get("todos", []):
            sample_todos.append((f.get("path"), t))
    if sample_todos:
        for p, t in sample_todos[:50]:
            parts.append(f"- `{p}` — {t}\n")
    else:
        parts.append("No TODO items found.\n")
    parts.append("\n")
    parts.append(_table_of_defs(ccg))
    parts.append("\n## Code Context Graph (visual)\n")
    parts.append(ca.ccg_to_mermaid(ccg))
    parts.append("\n")
    out = "\n".join(parts)
    if output_path:
        try:
            Path(output_path).write_text(out, encoding="utf-8")
        except Exception as e:
            out = f"<!-- write error: {e} -->\n\n" + out
    return out
