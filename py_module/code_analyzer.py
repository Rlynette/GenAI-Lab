"""py_module.code_analyzer

Lightweight static code analysis utilities and a simple Code Context Graph (CCG).
"""
from pathlib import Path
import os
import re
import ast
import json
from typing import List, Dict, Optional, Any, Tuple, Set
from collections import defaultdict

TODO_REGEX = re.compile(r'\bTODO\b[:\s-]?(.*)', re.IGNORECASE)

def find_code_files(root: Optional[str] = None, exts: Optional[List[str]] = None) -> List[Path]:
    root_p = Path(root) if root else Path.cwd()
    if exts is None:
        exts = [".py", ".jac", ".md", ".txt"]
    files: List[Path] = []
    for ext in exts:
        files.extend(root_p.rglob(f"*{ext}"))
    return sorted({p.resolve() for p in files})

def extract_todos(path: Path) -> List[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    todos: List[str] = []
    for m in TODO_REGEX.finditer(text):
        val = (m.group(1) or "").strip()
        todos.append(val if val else "TODO")
    return todos

def extract_top_level_defs_py(path: Path) -> List[Dict]:
    if not path.is_file() or path.suffix != ".py":
        return []
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
    except Exception:
        return []
    result: List[Dict] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            result.append({"type": "function", "name": node.name, "doc": ast.get_docstring(node) or ""})
        elif isinstance(node, ast.ClassDef):
            result.append({"type": "class", "name": node.name, "doc": ast.get_docstring(node) or ""})
    return result

def analyze_path(root: Optional[str] = None) -> Dict:
    files = find_code_files(root)
    out: Dict[str, Any] = {
        "path": str(Path(root).resolve()) if root else str(Path.cwd().resolve()),
        "files": [],
        "summary": {"todo_count": 0, "python_defs": 0}
    }
    todo_count = 0
    py_defs_count = 0
    for f in files:
        entry: Dict[str, Any] = {"path": str(f), "ext": f.suffix, "todos": [], "py_defs": []}
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

# ---- CCG utilities ----

def _module_name_from_path(repo_root: str, path: Path) -> str:
    try:
        rel = Path(path).resolve().relative_to(Path(repo_root).resolve())
    except Exception:
        rel = Path(path).resolve().name
    return str(rel).replace(os.sep, "/")

class _CCGVisitor(ast.NodeVisitor):
    def __init__(self, module_name: str):
        self.module = module_name
        self.funcs: Set[str] = set()
        self.classes: Set[str] = set()
        self.calls: List[Tuple[str, str]] = []
        self.instantiates: List[Tuple[str, str]] = []
        self.assigns: List[Tuple[str, str]] = []
        self.class_bases: Dict[str, List[str]] = {}
        self.current_function: Optional[str] = None
        self.current_class: Optional[str] = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        qual = f"{self.module}::{node.name}"
        self.funcs.add(qual)
        prev = self.current_function
        self.current_function = qual
        self.generic_visit(node)
        self.current_function = prev

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        qual = f"{self.module}::{node.name}"
        self.classes.add(qual)
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                parts = []
                cur = b
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                bases.append(".".join(reversed(parts)))
            else:
                try:
                    bases.append(ast.unparse(b))
                except Exception:
                    bases.append(str(b))
        self.class_bases[qual] = bases
        prev = self.current_class
        self.current_class = qual
        self.generic_visit(node)
        self.current_class = prev

    def visit_Call(self, node: ast.Call):
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        site = self.current_function or self.current_class or f"{self.module}::<module>"
        if name:
            self.calls.append((site, name))
            if name and name[0].isupper():
                self.instantiates.append((site, name))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                site = self.current_function or self.current_class or f"{self.module}::<module>"
                self.assigns.append((site, t.attr))
        self.generic_visit(node)

def analyze_ccg(repo_root: str) -> Dict[str, Any]:
    repo_root_p = Path(repo_root) if repo_root else Path.cwd()
    py_files = [p for p in find_code_files(str(repo_root_p), exts=[".py"])]
    nodes: Dict[str, Dict] = {}
    edges: List[Dict] = []
    visitors: Dict[Path, _CCGVisitor] = {}

    for p in py_files:
        try:
            src = p.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(src, filename=str(p))
        except Exception:
            continue
        module = _module_name_from_path(str(repo_root_p), p)
        v = _CCGVisitor(module)
        v.visit(tree)
        visitors[p] = v
        nodes.setdefault(f"mod:{module}", {"type": "module", "name": module, "file": str(p)})

    for p, v in visitors.items():
        module = v.module
        for fn in v.funcs:
            nodes.setdefault(f"fn:{fn}", {"type": "function", "name": fn.split("::")[-1], "qualname": fn, "module": module})
            edges.append({"from": f"mod:{module}", "to": f"fn:{fn}", "type": "defines", "label": "defines"})
        for cl in v.classes:
            nodes.setdefault(f"class:{cl}", {"type": "class", "name": cl.split("::")[-1], "qualname": cl, "module": module})
            edges.append({"from": f"mod:{module}", "to": f"class:{cl}", "type": "defines", "label": "defines"})

    for p, v in visitors.items():
        for cl_qual, bases in v.class_bases.items():
            for b in bases:
                base_nid = f"base:{b}"
                nodes.setdefault(base_nid, {"type": "base", "name": b})
                edges.append({"from": f"class:{cl_qual}", "to": base_nid, "type": "inherits", "label": "inherits"})

    for p, v in visitors.items():
        module = v.module
        name_to_node = defaultdict(list)
        for nid, nd in nodes.items():
            if nd.get("name"):
                name_to_node[nd["name"]].append(nid)
            if nd.get("qualname"):
                name_to_node[nd["qualname"]].append(nid)

        for caller_site, callee_name in v.calls:
            if f"fn:{caller_site}" in nodes:
                caller_nid = f"fn:{caller_site}"
            elif f"class:{caller_site}" in nodes:
                caller_nid = f"class:{caller_site}"
            else:
                caller_nid = f"mod:{module}"
            candidate_ids = name_to_node.get(callee_name, [])
            if candidate_ids:
                to_nid = candidate_ids[0]
            else:
                to_nid = f"fn:unresolved::{callee_name}"
                nodes.setdefault(to_nid, {"type": "unresolved", "name": callee_name})
            edges.append({"from": caller_nid, "to": to_nid, "type": "calls", "label": "calls"})

        for site, cls in v.instantiates:
            caller_nid = f"fn:{site}" if f"fn:{site}" in nodes else f"class:{site}" if f"class:{site}" in nodes else f"mod:{module}"
            class_candidates = name_to_node.get(cls, [])
            if class_candidates:
                class_nid = class_candidates[0]
            else:
                class_nid = f"class:unresolved::{cls}"
                nodes.setdefault(class_nid, {"type": "unresolved_class", "name": cls})
            edges.append({"from": caller_nid, "to": class_nid, "type": "instantiates", "label": "instantiates"})

    ccg = {"nodes": nodes, "edges": edges, "meta": {"files_analyzed": len(py_files)}}
    return ccg

def find_callers(ccg: Dict, target_name: str) -> List[Dict]:
    target_ids = [nid for nid, nd in ccg.get("nodes", {}).items()
                  if nd.get("name") == target_name or nd.get("qualname") == target_name]
    if not target_ids:
        target_ids = [nid for nid in ccg.get("nodes", {}) if target_name in nid]
    callers = []
    for e in ccg.get("edges", []):
        if e.get("type") == "calls" and e.get("to") in target_ids:
            nid = e.get("from")
            callers.append({"node_id": nid, "info": ccg["nodes"].get(nid)})
    return callers

def find_callees(ccg: Dict, source_name: str) -> List[Dict]:
    source_ids = [nid for nid, nd in ccg.get("nodes", {}).items()
                  if nd.get("name") == source_name or nd.get("qualname") == source_name]
    if not source_ids:
        source_ids = [nid for nid in ccg.get("nodes", {}) if source_name in nid]
    out = []
    for e in ccg.get("edges", []):
        if e.get("from") in source_ids and e.get("type") == "calls":
            out.append({"to": e.get("to"), "label": e.get("label")})
    return out

def ccg_to_mermaid(ccg: Dict, max_nodes: int = 300) -> str:
    lines = ["```mermaid", "graph TD"]
    count = 0
    for nid, nd in ccg.get("nodes", {}).items():
        if count >= max_nodes:
            break
        label = nd.get("name") or nid
        safe = nid.replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
        label = label.replace('"', "'")
        lines.append(f'    {safe}["{label}\\n({nd.get("type")})"]')
        count += 1
    for e in ccg.get("edges", []):
        src = e.get("from").replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
        dst = e.get("to").replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_")
        lbl = e.get("label", "")
        lbl = str(lbl).replace('"', "'")
        lines.append(f'    {src} -->|{lbl}| {dst}')
    lines.append("```")
    return "\n".join(lines)

# simple CLI for local invocation
def _cli():
    import argparse
    p = argparse.ArgumentParser(description="Lightweight code analyzer")
    p.add_argument("command", choices=["analyze"], help="analyze (generate summary)")
    p.add_argument("path", nargs="?", default=".", help="path to analyze (default: current dir)")
    p.add_argument("--exts", nargs="+", help="file extensions to include (e.g. .py .md)")
    args = p.parse_args()
    if args.command == "analyze":
        exts = args.exts if args.exts else None
        if exts:
            files = find_code_files(args.path, exts)
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

if __name__ == "__main__":
    _cli()
