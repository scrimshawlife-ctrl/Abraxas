from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any
import os
import subprocess
import time

from abx.util.logging import log, warn, err

def _run(cmd: list[str], cwd: Optional[Path] = None) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd) if cwd else None).decode("utf-8").strip()

def _try(cmd: list[str], cwd: Optional[Path] = None) -> bool:
    try:
        subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)
        return True
    except Exception:
        return False

def releases_root() -> Path:
    return Path(os.environ.get("ABX_RELEASES", "/opt/aal/abraxas_releases")).resolve()

def current_link() -> Path:
    return Path(os.environ.get("ABX_CURRENT", "/opt/aal/abraxas_current")).resolve()

def _git_sha(repo: Path) -> str:
    return _run(["git", "rev-parse", "--short", "HEAD"], cwd=repo)

def stage_release(repo_url: str, branch: str = "main") -> Path:
    rr = releases_root()
    rr.mkdir(parents=True, exist_ok=True)
    # clone into temp, then move to sha folder
    tmp = rr / f".tmp_{int(time.time())}"
    _try(["rm", "-rf", str(tmp)])
    ok = _try(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(tmp)])
    if not ok:
        raise RuntimeError("git_clone_failed")
    sha = _git_sha(tmp)
    dest = rr / sha
    if dest.exists():
        _try(["rm", "-rf", str(tmp)])
        return dest
    tmp.rename(dest)
    return dest

def run_smoke(release_dir: Path) -> bool:
    # Assume python env already set up, simplest: python -m abx.cli smoke
    return _try(["python", "-m", "abx.cli", "smoke"], cwd=release_dir)

def activate_release(release_dir: Path) -> None:
    cl = current_link()
    cl.parent.mkdir(parents=True, exist_ok=True)
    # atomic symlink swap: current -> new
    tmp_link = cl.parent / (cl.name + ".new")
    if tmp_link.exists() or tmp_link.is_symlink():
        tmp_link.unlink()
    tmp_link.symlink_to(release_dir)
    tmp_link.replace(cl)

def update_atomic(repo_url: str, branch: str = "main") -> Dict[str, Any]:
    log("update_start", repo_url=repo_url, branch=branch)
    prev = None
    try:
        if current_link().exists():
            prev = current_link().resolve()
    except Exception:
        prev = None

    staged = stage_release(repo_url, branch=branch)
    log("update_staged", path=str(staged))

    if not run_smoke(staged):
        err("update_smoke_failed", staged=str(staged))
        return {"ok": False, "error": "smoke_failed", "staged": str(staged), "prev": str(prev) if prev else None}

    try:
        activate_release(staged)
        log("update_activated", staged=str(staged))
        return {"ok": True, "staged": str(staged), "prev": str(prev) if prev else None}
    except Exception as e:
        err("update_activate_failed", error=str(e))
        # rollback
        if prev:
            try:
                activate_release(prev)
                warn("update_rolled_back", prev=str(prev))
            except Exception as e2:
                err("update_rollback_failed", error=str(e2))
        return {"ok": False, "error": "activate_failed", "staged": str(staged), "prev": str(prev) if prev else None}
