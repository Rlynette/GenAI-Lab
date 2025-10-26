import os, json, subprocess
from pathlib import Path

def clone_repo(url: str, dest_parent: str = "tmp_clones", shallow: bool = True, timeout: int = 120) -> str:
    if not url:
        url = os.environ.get("REPO_URL", "")
        if not url:
            raise ValueError("No repo URL provided and REPO_URL env var is not set")
    os.makedirs(dest_parent, exist_ok=True)
    name = url.rstrip("/").split("/")[-1]
    dest = os.path.join(dest_parent, name)
    if os.path.exists(dest):
        return dest
    if shallow:
        subprocess.check_call(["git", "clone", "--depth", "1", url, dest], timeout=timeout)
        return dest
    subprocess.check_call(["git", "clone", url, dest], timeout=timeout)
    return dest

def file_tree(root_path: str, depth: int = 2, ignore_dirs=None):
    root = Path(root_path)
    if not root.exists():
        return {}
    ignore_dirs = set(ignore_dirs or [".git", "node_modules", "env", "venv", "__pycache__"])
    def _walk(p: Path, d: int):
        res = {}
        try:
            for name in sorted(p.iterdir(), key=lambda x: x.name):
                if name.name in ignore_dirs:
                    continue
                if name.is_dir() and d > 0:
                    res[name.name] = {"type": "dir", "children": _walk(name, d - 1)}
                elif name.is_file():
                    try:
                        sz = name.stat().st_size
                    except Exception:
                        sz = 0
                    res[name.name] = {"type": "file", "size": sz}
        except Exception:
            pass
        return res
    return {root.name: {"type": "dir", "children": _walk(root, depth)}}

def save_json(obj, dest_path: str):
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
    return str(dest.resolve())
