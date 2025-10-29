from pathlib import Path
import os
import time
from typing import Dict, Any, List, Optional

# Optional Git dependency for cloning
try:
    from git import Repo, GitCommandError  # GitPython
except Exception:
    Repo = None
    GitCommandError = Exception


def get_repo_root(start: Optional[Path] = None) -> Path:
    """
    Walk up from `start` (or cwd) looking for a repo root indicator (.git, pyproject.toml, README.md).
    Returns a pathlib.Path (absolute). If nothing found, returns cwd().
    """
    p = Path(start or Path.cwd()).resolve()
    indicators = {".git", "pyproject.toml", "README.md", "setup.py"}
    for d in [p] + list(p.parents):
        for ind in indicators:
            if (d / ind).exists():
                return d
    return Path.cwd().resolve()


def list_repo_files(repo_root: Optional[Path] = None, recursive: bool = True) -> List[str]:
    """
    Return a list of relative file paths (strings) under repo_root.
    Excludes common virtualenvs, tmp_clones, and .git.
    """
    root = Path(repo_root or get_repo_root()).resolve()
    exclude_parts = {"tmp_clones", "env", ".venv", "venv", ".git", "__pycache__"}
    files: List[str] = []

    if recursive:
        iterator = root.rglob("*")
    else:
        iterator = root.iterdir()

    for p in iterator:
        if not p.is_file():
            continue
        # skip excluded directories if any path part matches
        if any(part in exclude_parts for part in p.relative_to(root).parts):
            continue
        files.append(str(p.relative_to(root)))
    return files


def file_tree(root: str | Path, depth: int = 2) -> Dict[str, Any]:
    """
    Return nested dict describing folder/file tree up to `depth`.
    Format:
    { root_name: { "type": "dir", "children": { ... } } }
    """
    root_p = Path(root).resolve()
    def build(p: Path, d: int):
        if d < 0:
            return None
        if p.is_file():
            return {"type": "file"}
        children = {}
        for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if child.name in {".git"}:
                # include .git as dir, but do not recurse too deep into internal git objects
                if d > 0:
                    children[child.name] = {"type": "dir", "children": {}}
                else:
                    children[child.name] = {"type": "dir", "children": {}}
                continue
            if child.is_dir():
                subtree = build(child, d - 1)
                children[child.name] = subtree if subtree is not None else {"type": "dir", "children": {}}
            else:
                children[child.name] = {"type": "file"}
        return {"type": "dir", "children": children}

    return {root_p.name: build(root_p, depth)}


def clone_repo(url: str, dest_parent: str = "tmp_clones", shallow: bool = True) -> str:
    """
    Clone `url` into dest_parent/<repo_name>-<timestamp>. Returns the path to the clone (string).
    Uses a shallow clone by default (depth=1) for speed.
    If GitPython is not installed, raises RuntimeError.
    """
    if not url:
        # fallback to environment variable if provided
        url = os.environ.get("REPO_URL", "")

    if not url:
        raise RuntimeError("No repository URL provided and REPO_URL not set.")

    dest_parent_p = Path(dest_parent)
    dest_parent_p.mkdir(parents=True, exist_ok=True)

    repo_name = url.rstrip("/").split("/")[-1] or "repo"
    timestamp = time.strftime("%Y%m%d%H%M%S")
    unique_name = f"{repo_name}-{timestamp}"
    dest = dest_parent_p / unique_name

    if Repo is None:
        raise RuntimeError("GitPython is required for clone_repo. Install with: pip install GitPython")

    try:
        # shallow clone if requested
        if shallow:
            Repo.clone_from(url, str(dest), depth=1)
        else:
            Repo.clone_from(url, str(dest))
        return str(dest)
    except GitCommandError as e:
        # raise a clearer runtime error for callers
        stderr_text = getattr(e, "stderr", "") or str(e)
        raise RuntimeError(f"git clone failed for url={url!r}. stderr: \n  stderr: {stderr_text!s}") from e
