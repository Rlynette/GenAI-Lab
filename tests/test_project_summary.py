import os
from py_module.project_summary import generate_project_summary

def test_project_summary_basic(tmp_path):
    # create a tiny project
    proj = tmp_path / "proj"
    proj.mkdir()
    readme = proj / "README.md"
    readme.write_text("# Project Title\n\nThis is a small project README.\n\nTODO: add more", encoding="utf-8")
    p = proj / "mod.py"
    p.write_text("def a():\n    pass\n# TODO: finish", encoding="utf-8")

    summary = generate_project_summary(str(proj))

    # required keys
    assert "project_root" in summary
    assert "readme_summary" in summary
    assert "code_analysis" in summary

    ca = summary["code_analysis"] or {}

    # tolerant check of TODO count in possible shapes
    todo_count = 0
    if isinstance(ca, dict):
        if "summary" in ca and isinstance(ca["summary"], dict):
            todo_count = ca["summary"].get("todo_count", 0)
        else:
            todo_count = ca.get("todo_count", 0)
    assert isinstance(todo_count, int)
    assert todo_count >= 1
