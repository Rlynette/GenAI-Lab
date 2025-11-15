"""
py_module.ccg - simple Code Context Graph (CCG) builder.

Functions:
- build_ccg(root, depth=1) -> dict with "nodes" and "edges"
- query_callers(graph, target) -> list of callers
- query_callees(graph, target) -> list of callees
- query_inherits(graph, target) -> dict with 'parents' and 'children'
"""
from pathlib import Path
import ast
from typing import Dict, List, Set

def _analyze_file(path: Path):
    """Return dict: {'functions': {name: set(called_names)}, 'classes': {name: [base_names]}}"""
    res = {"functions": {}, "classes": {}}
    try:
        src = path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
    except Exception:
        return res

    # collect top-level defs
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            name = node.name
            called = set()
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    # function call target could be Name or Attribute
                    func = sub.func
                    if isinstance(func, ast.Name):
                        called.add(func.id)
                    elif isinstance(func, ast.Attribute):
                        # attr could be method call e.g. obj.foo -> keep 'foo'
                        called.add(func.attr)
            res["functions"][name] = list(called)
        elif isinstance(node, ast.ClassDef):
            cname = node.name
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(b.attr)
                else:
                    bases.append(ast.dump(b))
            res["classes"][cname] = bases
    return res

def build_ccg(root: str = ".", depth: int = 1) -> Dict:
    """Scan .py files under root and build a simple graph."""
    root_p = Path(root)
    files = list(root_p.rglob("*.py"))
    nodes = set()
    edges = []  # list of dicts {from, to, type}

    func_map = {}  # name -> callers/callees
    inherits = []  # list of (child, parent)

    for f in files:
        info = _analyze_file(f)
        # functions
        for func, calls in info.get("functions", {}).items():
            nodes.add(func)
            # each call produces an edge func -> call (call type)
            for c in calls:
                edges.append({"from": func, "to": c, "type": "call"})
        # classes
        for cls, bases in info.get("classes", {}).items():
            nodes.add(cls)
            for b in bases:
                edges.append({"from": cls, "to": b, "type": "inherits"})
                inherits.append((cls, b))

    return {"nodes": sorted(list(nodes)), "edges": edges}

def query_callers(graph: Dict, target: str) -> List[str]:
    callers = set()
    for e in graph.get("edges", []):
        if e.get("type") == "call" and e.get("to") == target:
            callers.add(e.get("from"))
    return sorted(list(callers))

def query_callees(graph: Dict, target: str) -> List[str]:
    callees = set()
    for e in graph.get("edges", []):
        if e.get("type") == "call" and e.get("from") == target:
            callees.add(e.get("to"))
    return sorted(list(callees))

def query_inherits(graph: Dict, target: str) -> Dict:
    parents = set()
    children = set()
    for e in graph.get("edges", []):
        if e.get("type") == "inherits":
            if e.get("from") == target:
                parents.add(e.get("to"))
            if e.get("to") == target:
                children.add(e.get("from"))
    return {"parents": sorted(list(parents)), "children": sorted(list(children))}
