import os
from utils import repo_utils as ru

def test_get_repo_root():
    root = ru.get_repo_root()
    assert root.exists(), "Repo root path does not exist"
    assert ".git" in os.listdir(root), "No .git folder found in repo root"

def test_list_repo_files_nonempty():
    files = ru.list_repo_files()
    assert isinstance(files, list)
    assert len(files) > 0, "No tracked files found in repo"

# tests/test_repo_utils.py
# from utils.repo_utils import clone_repo

# def test_clone_repo():
#     path = clone_repo("https://github.com/jaseci-labs/jaseci")
#     assert path.endswith("jaseci")

