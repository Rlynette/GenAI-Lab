import subprocess
from pathlib import Path

def get_repo_root():
    """Return absolute path to the git repository root."""
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        return Path(root)
    except subprocess.CalledProcessError:
        return Path.cwd()

def list_repo_files():
    """Return all tracked files in this git repository."""
    try:
        output = subprocess.check_output(["git", "ls-files"], text=True)
        return output.splitlines()
    except subprocess.CalledProcessError:
        return []
