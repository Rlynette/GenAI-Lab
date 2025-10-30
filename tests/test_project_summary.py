from pathlib import Path
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
    assert "project_root" in summary
    assert "readme_summary" in summary
    assert "code_analysis" in summary
    assert summary["code_analysis"]["summary"]["todo_count"] >= 1
