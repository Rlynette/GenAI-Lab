"""
py_module.ccg_builder

Simple, fast Code Context Graph (CCG) builder and query helpers.
Designed to be small and predictable for demos/tests.

Functions:
- build_ccg(path) -> { "nodes": [<qname>...], "edges": [{"src":..., "tgt":..., "type":"call"|"inherit"}...] }
- query_callers(graph, target) -> [src_qname,...]
- query_callees(graph, target) -> [tgt_qname,...]
- query_inherits(graph, target) -> [child_qname,...]

Accepts either a file path (single source file) or a directory (walks .py files).
It only does best-effort extraction of simple call targets (Name or attr chains).
"""
from pathlib import Path
import ast
import json
from typing import Dict, List

def _qualname(module: str, name: str) -> str:
    return f"{module}.{name}" if module else name

def _get_call_name(node):
    # Try to extract a best-effort string for a Call node's function.
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        # produce dotted attribute name like obj.method
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))
    return None

def _visit_file(path: Path, module: str):
    """
    Returns two lists:
    - defs: list of qualified names defined in this file (functions and classes)
    - edges: list of ("caller", "callee", "type") where caller/callee are qnames
    """
    text = path.read_text(encoding="utf-8", errors="ignore")
    tree = ast.parse(text)
    defs = []
    edges = []

    # map node -> current enclosing function/class qualname
    class DefVisitor(ast.NodeVisitor):
        def __init__(self):
            self.stack = []  # stack of qualnames

        def visit_FunctionDef(self, node):
            cur_q = _qualname(module, ".".join(self.stack + [node.name]))
            defs.append(cur_q)
            # scan body for calls
            prev_stack = list(self.stack)
            self.stack.append(node.name)
            CallVisitor(self.stack, cur_q).visit(node)
            self.stack = prev_stack
            # continue visiting nested defs
            for c in node.body:
                self.generic_visit(c)

        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)

        def visit_ClassDef(self, node):
            cur_q = _qualname(module, ".".join(self.stack + [node.name]))
            defs.append(cur_q)
            # inheritance edges
            for base in node.bases:
                if isinstance(base, ast.Name):
                    edges.append((cur_q, base.id, "inherit"))
                elif isinstance(base, ast.Attribute):
                    # best-effort
                    edges.append((cur_q, _get_call_name(base), "inherit"))
            prev_stack = list(self.stack)
            self.stack.append(node.name)
            # visit methods
            for c in node.body:
                if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.visit_FunctionDef(c)
                else:
                    self.generic_visit(c)
            self.stack = prev_stack

    class CallVisitor(ast.NodeVisitor):
        def __init__(self, stack, cur_q):
            self.stack = stack
            self.cur_q = cur_q

        def visit_Call(self, node):
            name = _get_call_name(node.func)
            if name:
                # callee qname best-effort -- if it's unqualified, use name only
                edges.append((self.cur_q, name, "call"))
            # continue
            self.generic_visit(node)

    DefVisitor().visit(tree)
    return defs, edges

def build_ccg(path: str) -> Dict:
    p = Path(path)
    nodes = set()
    edges = []
    files = []
    if p.is_file():
        files = [p]
        module = p.stem
    else:
        # walk .py files (exclude venv/tmp_clones)
        files = [f for f in p.rglob("*.py") if "/env/" not in str(f) and "/tmp_clones/" not in str(f)]
        module = ""  # when directory, use qualified names including relative path
    for f in files:
        mod = module or ".".join(f.relative_to(Path.cwd()).with_suffix("").parts)
        try:
            defs, f_edges = _visit_file(f, mod)
        except Exception:
            # skip parse errors -- best-effort
            continue
        for d in defs:
            nodes.add(d)
        for src, tgt, typ in f_edges:
            edges.append({"src": src, "tgt": tgt, "type": typ})
            # also ensure nodes exist for targets (best-effort)
            nodes.add(src)
            nodes.add(tgt)
    return {"nodes": sorted(nodes), "edges": edges}

def query_callers(graph: Dict, target: str) -> List[str]:
    # callers are edges where tgt matches target or endswith '.target'
    res = []
    for e in graph.get("edges", []):
        if e["type"] == "call":
            if e["tgt"] == target or e["tgt"].endswith("." + target):
                res.append(e["src"])
    return sorted(set(res))

def query_callees(graph: Dict, target: str) -> List[str]:
    # callees called by target
    res = []
    for e in graph.get("edges", []):
        if e["type"] == "call":
            if e["src"] == target or e["src"].endswith("." + target):
                res.append(e["tgt"])
    return sorted(set(res))

def query_inherits(graph: Dict, target: str) -> List[str]:
    res = []
    for e in graph.get("edges", []):
        if e["type"] == "inherit":
            if e["tgt"] == target or e["tgt"].endswith("." + target):
                res.append(e["src"])
    return sorted(set(res))

if __name__ == "__main__":
    import sys, json
    path = sys.argv[1] if len(sys.argv) > 1 else "py_module/code_analyzer.py"
    g = build_ccg(path)
    print(json.dumps({"nodes": len(g["nodes"]), "edges": len(g["edges"])}, indent=2))
