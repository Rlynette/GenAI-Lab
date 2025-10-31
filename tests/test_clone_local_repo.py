import os
import subprocess
from pathlib import Path
from utils import repo_utils as ru

def test_clone_local(tmp_path, monkeypatch):
    # Create a small source repo with a commit
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("hello")
    env = os.environ.copy()
    # Provide commit metadata to avoid global config dependency
    env.update({
        "GIT_AUTHOR_NAME": "CI Test",
        "GIT_AUTHOR_EMAIL": "ci@example.com",
        "GIT_COMMITTER_NAME": "CI Test",
        "GIT_COMMITTER_EMAIL": "ci@example.com",
    })
    subprocess.run(["git", "init"], cwd=str(src), check=True, env=env)
    subprocess.run(["git", "add", "."], cwd=str(src), check=True, env=env)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(src), check=True, env=env)

    # Clone from the local path (no network)
    dest_parent = tmp_path / "dest"
    dest_parent.mkdir()
    dest_path = ru.clone_repo(str(src), dest_parent=str(dest_parent), shallow=False, timeout=30)
    assert Path(dest_path).exists()
    tree = ru.file_tree(dest_path, depth=1)
    assert any("README" in k or "README.md" in str(tree) for k in [dest_path.split("/")[-1]])
