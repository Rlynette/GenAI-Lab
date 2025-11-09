"""
py_module.code_analyzer

Lightweight static code analysis utilities.

Functions:
- find_code_files(root=None, exts=None) -> list[Path]
- extract_todos(path) -> list[str]
- extract_top_level_defs_py(path) -> list[dict]

Also provides a simple CLI: `python -m py_module.code_analyzer analyze <path>`
which prints JSON summary for the path.
"""
from pathlib import Path
import re
import ast
import json
from typing import List, Dict, Optional

TODO_REGEX = re.compile(r'\bTODO\b[:\s-]?(.*)', re.IGNORECASE)

def find_code_files(root: Optional[str] = None, exts: Optional[List[str]] = None) -> List[Path]:
    """Return a sorted list of Path objects matching extensions under root."""
    root_p = Path(root) if root else Path.cwd()
    if exts is None:
        exts = [".py", ".jac", ".md", ".txt"]
    files = []
    for ext in exts:
        files.extend(root_p.rglob(f"*{ext}"))
    # return normalized sorted list
    return sorted({p.resolve() for p in files})

def extract_todos(path: Path) -> List[str]:
    """Extract TODO items (text after TODO) from a file."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    todos = []
    for m in TODO_REGEX.finditer(text):
        # capture group (may be empty) and strip
        val = m.group(1).strip()
        todos.append(val if val else "TODO")
    return todos

def extract_top_level_defs_py(path: Path) -> List[Dict]:
    """For Python files, return top-level functions/classes with docstrings."""
    if not path.is_file() or path.suffix != ".py":
        return []
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
    except Exception:
        return []
    result = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            result.append({"type": "function", "name": node.name, "doc": ast.get_docstring(node) or ""})
        elif isinstance(node, ast.ClassDef):
            result.append({"type": "class", "name": node.name, "doc": ast.get_docstring(node) or ""})
    return result

def analyze_path(root: Optional[str] = None) -> Dict:
    """Run a lightweight analysis for the path: files, todos, and python defs."""
    files = find_code_files(root)
    out = {"path": str(Path(root).resolve()) if root else str(Path.cwd().resolve()), "files": [], "summary": {"todo_count": 0, "python_defs": 0}}
    todo_count = 0
    py_defs_count = 0
    for f in files:
        entry = {"path": str(f), "ext": f.suffix, "todos": [], "py_defs": []}
        todos = extract_todos(f)
        if todos:
            entry["todos"] = todos
            todo_count += len(todos)
        if f.suffix == ".py":
            defs = extract_top_level_defs_py(f)
            if defs:
                entry["py_defs"] = defs
                py_defs_count += len(defs)
        out["files"].append(entry)
    out["summary"]["todo_count"] = todo_count
    out["summary"]["python_defs"] = py_defs_count
    return out

def _cli():
    import argparse
    p = argparse.ArgumentParser(description="Lightweight code analyzer")
    p.add_argument("command", choices=["analyze"], help="analyze (generate summary)")
    p.add_argument("path", nargs="?", default=".", help="path to analyze (default: current dir)")
    p.add_argument("--exts", nargs="+", help="file extensions to include (e.g. .py .md)")
    args = p.parse_args()
    if args.command == "analyze":
        exts = args.exts if args.exts else None
        # if custom exts provided, pass them to find_code_files by temporarily overriding default
        if exts:
            # call find_code_files with the exts param
            files = find_code_files(args.path, exts)
            # build output similarly but only for those files (simple)
            out = {"path": str(Path(args.path).resolve()), "files": [], "summary": {}}
            todos, py_defs = 0, 0
            for f in files:
                e = {"path": str(f), "ext": f.suffix, "todos": extract_todos(f)}
                if f.suffix == ".py":
                    defs = extract_top_level_defs_py(f)
                    e["py_defs"] = defs
                    py_defs += len(defs)
                todos += len(e.get("todos", []))
                out["files"].append(e)
            out["summary"] = {"todo_count": todos, "python_defs": py_defs}
        else:
            out = analyze_path(args.path)
        print(json.dumps(out, indent=2))
    else:
        p.print_help()

if __name__ == "__main__":
    _cli()
