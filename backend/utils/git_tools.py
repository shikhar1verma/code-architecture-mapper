import os
import shutil
import subprocess
from typing import Tuple
from backend.config import TMP_DIR

IGNORE_DIRS = {".git", "node_modules", "dist", "build", ".next", ".venv", "venv", "__pycache__", "migrations", "coverage", "snapshots", "vendor"}


def shallow_clone(repo_url: str) -> Tuple[str, str]:
    """Clone with depth=1 to a unique tmp dir; return (path, commit_sha). Requires git installed."""
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    target = os.path.join(TMP_DIR, f"{repo_name}")
    if os.path.exists(target):
        shutil.rmtree(target)
    subprocess.run(["git", "clone", "--depth", "1", repo_url, target], check=True)
    sha = subprocess.check_output(["git", "-C", target, "rev-parse", "HEAD"]).decode().strip()
    return target, sha


def walk_repo(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        # prune ignore dirs
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            yield os.path.join(dirpath, f) 