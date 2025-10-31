import os
import subprocess
from pathlib import Path
from py_module import repo_utils as ru

def init_local_repo(path: Path):
    """Create a simple local git repo with one file and a commit."""
    path.mkdir(parents=True, exist_ok=True)
    subprocess.check_call(["git", "init"], cwd=path)
    subprocess.check_call(["git", "config", "user.email", "ci@example.com"], cwd=path)
    subprocess.check_call(["git", "config", "user.name", "CI Runner"], cwd=path)
    (path / "README.md").write_text("# test repo\n")
    subprocess.check_call(["git", "add", "README.md"], cwd=path)
    subprocess.check_call(["git", "commit", "-m", "initial commit"], cwd=path)
    return path

def test_clone_repo(tmp_path):
    # create origin repo inside pytest temp dir
    origin = tmp_path / "origin_repo"
    init_local_repo(origin)

    origin_url = str(origin.resolve())

    # IMPORTANT: clone into a dest inside tmp_path so we don't create tmp_clones in project root
    dest_parent = tmp_path / "clones"
    cloned = ru.clone_repo(origin_url, dest_parent=str(dest_parent), shallow=True)

    assert cloned is not None
    assert os.path.isdir(cloned), f"Cloned path not found: {cloned}"
    assert os.path.exists(os.path.join(cloned, "README.md"))
