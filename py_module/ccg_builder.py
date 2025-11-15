"""
py_module.ccg_builder

Simple, robust Code Context Graph (CCG) builder and query helpers.

Functions:
- build_ccg(path) -> { "nodes": [...], "edges": [{ "src": ..., "tgt": ..., "type": "call"|"inherit" }, ...] }
- query_callers(graph, target) -> [src_qname,...]
- query_callees(graph, target) -> [tgt_qname,...]
- query_inherits(graph, target) -> [child_qname,...]

Accepts a file path or directory. Skips obvious virtualenv/tmp folders.
"""
from pathlib import Path
import ast
from typing import Dict, List, Set

IGNORE_DIRS = {"env", ".venv", ".git", "tmp_clones", "venv", "__pycache__"}

def _qualname(module: str, name: str) -> str:
    return f"{module}.{name}" if module else name

def _get_attr_name(node):
    """Return dotted name for Attribute or Name nodes, best-effort."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        parts.reverse()
        return ".".join(parts)
    return None

def _get_call_name(node):
    """Get a best-effort string for a Call.func node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _get_attr_name(node)
    return None

def _iter_py_files(root: Path):
    if root.is_file() and root.suffix == ".py":
        yield root
        return
    for p in root.rglob("*.py"):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        yield p

def build_ccg(path: str) -> Dict:
    """
    Build a small code-context graph from path (file or directory).
    Returns {"nodes": [qname...], "edges": [{"src":..., "tgt":..., "type":"call"|"inherit"}...]}
    """
    repo_root = Path.cwd().resolve()
    root = Path(path)
    # accept file, dir, or module-ish string
    if not root.exists():
        # fallback: try treat as module-ish path under repo
        root = repo_root / path

    nodes: Set[str] = set()
    edges: List[Dict] = []

    for f in _iter_py_files(root):
        try:
            f_resolved = f.resolve()
        except Exception:
            f_resolved = f

        # module name: try relative to repo root, otherwise use stem
        try:
            module = ".".join(f_resolved.relative_to(repo_root).with_suffix("").parts)
        except Exception:
            module = f_resolved.stem

        src_text = f_resolved.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(src_text)
        except Exception:
            # skip unparsable file
            continue

        # record top-level functions and classes (qualnames)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                q = _qualname(module, node.name)
                nodes.add(q)
            elif isinstance(node, ast.ClassDef):
                q = _qualname(module, node.name)
                nodes.add(q)
                # inheritance edges
                for base in node.bases:
                    base_name = None
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = _get_attr_name(base)
                    if base_name:
                        # record base as node (best effort) and inherit edge
                        nodes.add(base_name)
                        edges.append({"src": base_name, "tgt": q, "type": "inherit"})

        # traverse functions and find Call nodes (calls from function -> target)
        class CallVisitor(ast.NodeVisitor):
            def __init__(self, module_name):
                self.module_name = module_name
                self.current_fn = None

            def visit_FunctionDef(self, node):
                self.current_fn = _qualname(self.module_name, node.name)
                nodes.add(self.current_fn)
                self.generic_visit(node)
                self.current_fn = None

            def visit_ClassDef(self, node):
                # methods inside class -> qualify as Class.method
                prev = self.current_fn
                self.current_fn = _qualname(self.module_name, node.name)
                # still traverse body to catch nested defs
                self.generic_visit(node)
                self.current_fn = prev

            def visit_Call(self, node):
                try:
                    name = _get_call_name(node.func)
                    if name:
                        # build a best-effort target qualname: if it's dotted use as-is,
                        # otherwise attach module only if ambiguous
                        tgt = name
                        # record nodes and edges
                        nodes.add(tgt)
                        if self.current_fn:
                            edges.append({"src": self.current_fn, "tgt": tgt, "type": "call"})
                except Exception:
                    pass
                self.generic_visit(node)

        CallVisitor(module).visit(tree)

    return {"nodes": sorted(nodes), "edges": edges}

def query_callers(graph: Dict, target: str) -> List[str]:
    """Return list of unique call-source qualnames that call `target` (match by final name)."""
    out = []
    for e in graph.get("edges", []):
        if e.get("type") != "call":
            continue
        tgt = e.get("tgt", "")
        if tgt.split(".")[-1] == target or tgt == target:
            src = e.get("src")
            if src and src not in out:
                out.append(src)
    return out

def query_callees(graph: Dict, target: str) -> List[str]:
    """Return list of unique call-target qualnames called by `target` sources."""
    out = []
    for e in graph.get("edges", []):
        if e.get("type") != "call":
            continue
        if e.get("src","").split(".")[-1] == target or e.get("src","") == target:
            tgt = e.get("tgt")
            if tgt and tgt not in out:
                out.append(tgt)
    return out

def query_inherits(graph: Dict, target: str) -> List[str]:
    """Return list of classes that inherit from `target` (match by final name)."""
    out = []
    for e in graph.get("edges", []):
        if e.get("type") != "inherit":
            continue
        if e.get("src","").split(".")[-1] == target or e.get("src","") == target:
            child = e.get("tgt")
            if child and child not in out:
                out.append(child)
    return out
