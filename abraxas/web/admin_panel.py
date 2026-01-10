from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..io.config import load_user_config
from ..io.storage import DEFAULT_ROOT, StoragePaths, today_iso
from ..kite.admin import add_candidate, list_ingests, load_candidates


router = APIRouter(prefix="/admin", tags=["admin"])


class CandidateBody(BaseModel):
    category: str
    item: Dict[str, Any]
    day: Optional[str] = None
    root: Optional[str] = None


def _paths(root: Optional[str]) -> StoragePaths:
    base = Path(root).expanduser() if root else DEFAULT_ROOT
    return StoragePaths(root=base)


def _require_admin(paths: StoragePaths) -> None:
    uc = load_user_config(paths)
    if not uc.admin:
        raise HTTPException(403, "admin disabled in local config")


@router.get("/health")
def admin_health(root: Optional[str] = None):
    paths = _paths(root)
    _require_admin(paths)
    return {"ok": True}


@router.get("/kite/{day}/ingest")
def kite_ingest_list(day: str, root: Optional[str] = None):
    paths = _paths(root)
    _require_admin(paths)
    return {"day": day, "ingest": list_ingests(paths, day)}


@router.get("/kite/{day}/candidates")
def kite_candidates(day: str, root: Optional[str] = None):
    paths = _paths(root)
    _require_admin(paths)
    return {"day": day, "candidates": load_candidates(paths, day)}


@router.post("/kite/candidates")
def kite_add_candidate(body: CandidateBody):
    paths = _paths(body.root)
    _require_admin(paths)
    day = body.day or today_iso()
    updated = add_candidate(paths, day, body.category, body.item)
    return {"ok": True, "day": day, "candidates": updated}
