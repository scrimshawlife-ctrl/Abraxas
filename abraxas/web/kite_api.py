from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..io.config import load_user_config
from ..io.storage import DEFAULT_ROOT, StoragePaths, today_iso
from ..kite.ingest import ensure_candidates, ingest_note


router = APIRouter(prefix="/kite", tags=["kite"])


class KiteIngestBody(BaseModel):
    kind: str
    domain: str
    tags: List[str] = []
    text: str
    source: Optional[str] = None
    day: Optional[str] = None
    root: Optional[str] = None


@router.post("/ingest")
def kite_ingest(body: KiteIngestBody):
    root = Path(body.root).expanduser() if body.root else DEFAULT_ROOT
    paths = StoragePaths(root=root)
    uc = load_user_config(paths)
    if not uc.admin:
        raise HTTPException(403, "admin disabled in local config")

    day = body.day or today_iso()
    ingest_note(paths, day, body.kind, body.domain, body.tags, body.text, body.source)
    ensure_candidates(paths, day)
    return {"ok": True, "day": day}
