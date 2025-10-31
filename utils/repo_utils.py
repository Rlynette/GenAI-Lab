#!/usr/bin/env python3
"""
Hardened repo helper utilities.

Functions:
- clone_repo(url, dest_parent="tmp_clones", shallow=True, timeout=120, force=False) -> str (path)
- file_tree(path, depth=2) -> dict
- get_repo_root() -> pathlib.Path
- list_repo_files(repo_root=None) -> list[str]
"""
from __future__ import annotations
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime

# Simple URL checker: accept http(s) and git@... patterns or local paths
_GIT_SSH_RE = re.compile(r"^(?:git@|ssh://)")
_GIT_HTTP_SCHEMES = {"http", "https", "git", "ssh"}


def _is_valid_repo_url(url: str) -> bool:
    if not url:
        return False
    # local path (absolute or relative)
    p = Path(url)
    if p.exists():
        return True
    # http/https/git urls
    if _GIT_SSH_RE.match(url):
        return True
    parsed = urlparse(url)
    return parsed.scheme in _GIT_HTTP_SCHEMES and bool(parsed.netloc)


def _normalize_repo_name(url: str) -> str:
    # remove trailing .git and any trailing slash
    name = Path(urlparse(url).path).name if "://" in url else Path(url).name
    name = name.rstrip("/")
    if name.endswith(".git"):
        name = name[: -len(".git")]
    if not name:
        name = "repo"
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", name)


def clone_repo(
    url: str,
    dest_parent: str = "tmp_clones",
    shallow: bool = True,
    timeout: int = 120,
    force: bool = False,
) -> str:
    """
    Clone `url` into dest_parent/<repo_name>-<timestamp> and return the path.
    - If url is empty, will try environment variable REPO_URL.
    - Validates URL input and provides helpful error messages.
    - Uses subprocess git so this works without GitPython.
    - If destination exists:
        - if force=True: remove it and reclone
        - else: create a unique suffix (timestamp) so clones are idempotent
    """
    if not url:
        url = os.environ.get("REPO_URL", "").strip()

    if not _is_valid_repo_url(url):
        raise ValueError(f"Invalid or empty repo url: {url!r}")

    dest_parent_p = Path(dest_parent)
    dest_parent_p.mkdir(parents=True, exist_ok=True)

    repo_name = _normalize_repo_name(url)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")[:-3]
    dest = dest_parent_p / f"{repo_name}-{timestamp}"

    # If force and dest exists for some reason, remove it
    if dest.exists() and force:
        shutil.rmtree(dest)

    # run git clone via subprocess for timeout support
    cmd = ["git", "clone"]
    if shallow:
        cmd += ["--depth", "1"]
    cmd += [str(url), str(dest)]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            timeout=timeout,
            check=True,
        )
        # small sleep to ensure FS has flushed (avoid race in CI)
        time.sleep(0.05)
        return str(dest)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        raise RuntimeError(f"git clone failed for url={url!r}. stderr: \n  stderr: {stderr!s}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"git clone timed out for url={url!r} after {timeout}s") from e


def _node_repr(path: Path, depth: int) -> Dict[str, Any]:
    if path.is_file():
        return {"type": "file"}
    if depth <= 0:
        return {"type": "dir", "children": {}}
    children: Dict[str, Any] = {}
    try:
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            children[child.name] = _node_repr(child, depth - 1)
    except PermissionError:
        # skip unreadable entries
        pass
    return {"type": "dir", "children": children}


def file_tree(root: str | Path, depth: int = 2) -> Dict[str, Any]:
    """
    Return a nested dict representing the folder/file structure up to `depth`.
    Format: { root_name: {...} } to match tests/examples.
    """
    p = Path(root)
    if not p.exists():
        raise FileNotFoundError(f"Path does not exist: {p}")
    return {p.name: _node_repr(p, depth)}


def get_repo_root(start: Optional[str] = None) -> Path:
    """
    Walk upward from `start` (or cwd) to find a folder containing `.git`.
    Returns the Path where `.git` exists or current working dir if not found.
    """
    start_p = Path(start) if start else Path.cwd()
    for p in [start_p] + list(start_p.parents):
        if (p / ".git").exists():
            return p
    # Fallback to cwd for tests that expect a path
    return Path.cwd()


def list_repo_files(repo_root: Optional[str] = None) -> list[str]:
    """
    Return list of files (relative to repo root). Excludes virtual env dir and tmp clones.
    """
    root = Path(repo_root) if repo_root else get_repo_root()
    items = []
    for p in root.rglob("*"):
        try:
            if p.is_file():
                # ignore typical virtualenv and tmp clone dirs
                if "env" in p.parts or "tmp_clones" in p.parts or ".venv" in p.parts:
                    continue
                items.append(str(p.relative_to(root)))
        except Exception:
            continue
    return sorted(items)
