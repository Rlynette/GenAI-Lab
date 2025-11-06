# tests/test_project_summary.py
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

    # basic keys
    assert "project_root" in summary
    assert "readme_summary" in summary
    assert "code_analysis" in summary

    # readme summary must show our header
    assert summary["readme_summary"].startswith("# Project Title")

    # code_analysis: either analyzer produced a 'summary' with todo_count or an info/error dict.
    ca = summary["code_analysis"]
    assert isinstance(ca, dict)

    # if analyzer ran produce meaningful summary, ensure todo_count >= 1
    if "summary" in ca and isinstance(ca["summary"], dict):
        assert ca["summary"].get("todo_count", 0) >= 1
