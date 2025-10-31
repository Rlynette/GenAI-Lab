import os
import subprocess
from pathlib import Path
from utils import repo_utils as ru

def test_get_repo_root_local(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("hi")
    # init a git repo (no commit needed) so .git exists
    subprocess.run(["git", "init"], cwd=str(src), check=True)
    root = ru.get_repo_root(str(src))
    assert Path(root).exists()
    assert (Path(root) / ".git").exists()

def test_list_repo_files_local(tmp_path):
    src = tmp_path / "src2"
    src.mkdir()
    (src / "README.md").write_text("hello")
    subprocess.run(["git", "init"], cwd=str(src), check=True)
    files = ru.list_repo_files(repo_root=str(src))
    assert any("README.md" in f or "README" in f for f in files)
