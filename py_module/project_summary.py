# py_module/project_summary.py
"""
Builds a small project summary used by walkers / tests.

Exposes:
- build_project_summary(path) -> dict
- generate_project_summary(path) -> dict  (compat)
"""
from pathlib import Path
import os
from typing import List, Dict, Optional

# optional import: if present, we'll call analyze_path(path)
try:
    from py_module import code_analyzer as code_analyzer_module  # type: ignore
except Exception:
    code_analyzer_module = None

def _list_readmes(root: str) -> List[Path]:
    """Return list of README-like files (case-insensitive) under root (shallow)."""
    root_p = Path(root)
    if not root_p.exists():
        return []
    readmes = []
    # walk and pick files whose name startswith 'readme' (case-insensitive)
    for p in root_p.rglob("*"):
        if p.is_file() and p.name.lower().startswith("readme"):
            readmes.append(p)
    # prefer README.md at repo root if present
    readmes = sorted(readmes, key=lambda p: (0 if p.parent == root_p else 1, str(p)))
    return readmes

def _summarize_readme(path: Path) -> str:
    """Extract a tiny summary from a README: first markdown header (# ...) or first non-empty line."""
    try:
        txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    # try to find a markdown H1 or H2 header
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s
    # fallback: first non-empty line (short)
    for line in txt.splitlines():
        s = line.strip()
        if s:
            return s[:200]
    return ""

def build_project_summary(path: Optional[str] = None) -> Dict:
    """Build a project summary for `path` (path may be repo root or empty -> cwd)."""
    root = Path(path or ".").resolve()
    repo_path = str(root)
    # collect readmes
    readme_files = _list_readmes(repo_path)
    readmes = []
    for p in readme_files:
        # make path relative to repo_root when possible
        try:
            rel = os.path.relpath(str(p), repo_path)
        except Exception:
            rel = p.name
        readmes.append({"path": rel, "summary": _summarize_readme(p)})
    readme_summary = readmes[0]["summary"] if readmes else ""
    summary = {
        "repo_path": repo_path,
        "project_root": repo_path,
        "num_readmes": len(readmes),
        "readme_summary": readme_summary,
        "readmes": readmes,
    }

    # non-fatal code analysis integration (if analyzer available)
    code_analysis = None
    if code_analyzer_module and hasattr(code_analyzer_module, "analyze_path"):
        try:
            code_analysis = code_analyzer_module.analyze_path(repo_path)
            # ensure shape: analyzer should provide 'summary' dict; if not, normalize a bit
            if not isinstance(code_analysis, dict):
                code_analysis = {"error": "analyzer returned non-dict"}
            else:
                if "summary" not in code_analysis:
                    # try to compute small summary from returned shape
                    todo_count = 0
                    py_defs = 0
                    if isinstance(code_analysis.get("files"), list):
                        for f in code_analysis["files"]:
                            todo_count += len(f.get("todos", [])) if isinstance(f.get("todos"), list) else 0
                            if isinstance(f.get("py_defs"), list):
                                py_defs += len(f.get("py_defs", []))
                    code_analysis["summary"] = {"todo_count": todo_count, "python_defs": py_defs}
        except Exception as e:
            code_analysis = {"error": f"code_analyzer failed: {e}"}
    else:
        code_analysis = {"info": "code_analyzer not available"}

    summary["code_analysis"] = code_analysis
    return summary

# compatibility alias
generate_project_summary = build_project_summary
