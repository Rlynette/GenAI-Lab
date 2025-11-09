from pathlib import Path
from py_module import code_analyzer as ca

def test_find_and_extract(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    p1 = repo / "a.py"
    p1.write_text('''"""module doc"""\n# TODO: improve function\n\ndef foo():\n    """foo doc"""\n    return 1\n''', encoding="utf-8")
    p2 = repo / "README.md"
    p2.write_text("Project README\n\nTODO: write usage\n", encoding="utf-8")
    files = ca.find_code_files(str(repo), exts=[".py", ".md"])
    assert any(p1.name == f.name for f in files)
    todos1 = ca.extract_todos(p1)
    assert any("improve" in t.lower() or "TODO" in t.upper() for t in todos1)
    py_defs = ca.extract_top_level_defs_py(p1)
    assert any(d["name"] == "foo" for d in py_defs)
    summary = ca.analyze_path(str(repo))
    assert summary["summary"]["todo_count"] >= 1
    assert isinstance(summary["files"], list)
