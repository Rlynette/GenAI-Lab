# utils/repo_utils.py
from pathlib import Path
import os
import shutil
import subprocess
import uuid
import datetime
from typing import Dict, Any

# Optional GitPython
try:
    from git import Repo, GitCommandError
except Exception:
    Repo = None
    GitCommandError = Exception

def _unique_dest(dest_parent: Path, repo_name: str) -> Path:
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    return dest_parent / f"{repo_name}-{ts}-{suffix}"

def clone_repo(url: str, dest_parent: str = "tmp_clones", shallow: bool = True, timeout: int = 300) -> str:
    """
    Clone `url` into dest_parent/<repo_name> (unique if collision).
    - shallow=True => --depth=1 (default)
    - If url is empty, fallback to REPO_URL env var.
    - Returns absolute path to clone (string).
    """
    final_url = (url or "").strip() or os.environ.get("REPO_URL", "").strip()
    if not final_url:
        raise RuntimeError("No repo URL provided and REPO_URL env var is not set.")

    dest_parent_p = Path(dest_parent)
    dest_parent_p.mkdir(parents=True, exist_ok=True)

    repo_name = Path(final_url.rstrip("/")).name or "repo"
    dest = dest_parent_p / repo_name

    # avoid collisions: if dest exists, use a unique name
    if dest.exists():
        dest = _unique_dest(dest_parent_p, repo_name)

    try:
        if Repo is None:
            # fallback to git CLI
            cmd = ["git", "clone"]
            if shallow:
                cmd += ["--depth", "1"]
            cmd += [final_url, str(dest)]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        else:
            if shallow:
                Repo.clone_from(final_url, str(dest), depth=1)
            else:
                Repo.clone_from(final_url, str(dest))
        return str(dest)
    except Exception as e:
        # cleanup any partial clone
        try:
            if dest.exists():
                shutil.rmtree(dest)
        except Exception:
            pass
        stderr_text = ""
        if hasattr(e, "stderr") and e.stderr:
            stderr_text = e.stderr.decode(errors="ignore") if isinstance(e.stderr, (bytes, bytearray)) else str(e.stderr)
        raise RuntimeError(f"git clone failed for url={final_url!r}. stderr: \n  stderr: {stderr_text}") from e

# Simple file_tree implementation (if you need one)
def file_tree(root: str, depth: int = 2) -> Dict[str, Any]:
    """
    Return a nested dict showing files/dirs up to `depth`.
    """
    def _walk(p: Path, d: int):
        if d < 0:
            return None
        if p.is_file():
            return {"type": "file"}
        children = {}
        for c in sorted(p.iterdir()):
            if c.is_dir():
                children[c.name] = {"type": "dir", "children": _walk(c, d-1) or {}}
            else:
                children[c.name] = {"type": "file"}
        return children

    p = Path(root)
    return {p.name: {"type": "dir", "children": _walk(p, depth-1) or {}}}# # py_module/repo_utils.py
# from pathlib import Path
# import os
# import shutil
# import time
# from urllib.parse import urlparse
# from typing import Dict, Any

# try:
#     from git import Repo, GitCommandError
# except Exception:
#     Repo = None
#     GitCommandError = Exception


# def _is_valid_url(url: str) -> bool:
#     if not url:
#         return False
#     p = urlparse(url)
#     # Allow http(s) and file schemes (file://) for local tests.
#     return p.scheme in ("http", "https", "file", "ssh", "git") or ":" in url


# def _unique_dest(dest_parent: Path, repo_name: str) -> Path:
#     # create dest parent
#     dest_parent.mkdir(parents=True, exist_ok=True)
#     # create unique folder with timestamp
#     ts = time.strftime("%Y%m%d%H%M%S")
#     final = dest_parent / f"{repo_name}-{ts}"
#     return final


# def clone_repo(url: str, dest_parent: str = "tmp_clones", shallow: bool = True) -> str:
#     """
#     Clone `url` into dest_parent/<repo_name>-<timestamp>.
#     Returns path to the clone (string).
#     - If url is empty uses REPO_URL env var.
#     - Accepts file:// local repos (useful for tests).
#     - Raises RuntimeError on error with helpful message.
#     """
#     # require GitPython
#     if Repo is None:
#         raise RuntimeError("GitPython not installed. Run: pip install GitPython")

#     final_url = url or os.environ.get("REPO_URL", "")
#     if not final_url:
#         raise RuntimeError("No repo URL provided and REPO_URL not set in environment.")
#     if not _is_valid_url(final_url):
#         raise RuntimeError(f"Invalid repository URL: {final_url!r}")

#     dest_parent_p = Path(dest_parent)
#     repo_name = Path(urlparse(final_url).path).name or "repo"

#     dest = _unique_dest(dest_parent_p, repo_name)
#     try:
#         # shallow clone if requested (depth=1)
#         if shallow:
#             Repo.clone_from(final_url, str(dest), depth=1)
#         else:
#             Repo.clone_from(final_url, str(dest))
#         return str(dest)
#     except GitCommandError as e:
#         # cleanup on failure if the folder exists
#         if dest.exists():
#             try:
#                 shutil.rmtree(dest)
#             except Exception:
#                 pass
#         stderr_text = getattr(e, "stderr", None) or str(e)
#         raise RuntimeError(f"git clone failed for url={final_url!r}. stderr: \n  stderr: {stderr_text!s}") from e


# def file_tree(root: str, depth: int = 2) -> Dict[str, Any]:
#     """
#     Return a nested dict representing the file tree under `root` up to `depth`.
#     Format:
#     { "<rootname>": { "type": "dir", "children": { ... } } }
#     """
#     root_p = Path(root)
#     if not root_p.exists():
#         return {}

#     def _build(path: Path, d: int):
#         if path.is_file():
#             return {"type": "file"}
#         if d <= 0:
#             return {"type": "dir", "children": {}}
#         children = {}
#         for p in sorted(path.iterdir(), key=lambda x: x.name):
#             try:
#                 children[p.name] = _build(p, d - 1)
#             except Exception:
#                 children[p.name] = {"type": "file"}
#         return {"type": "dir", "children": children}

#     return {root_p.name: _build(root_p, depth)}
