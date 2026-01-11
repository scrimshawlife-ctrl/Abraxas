from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

from ..io.config import load_user_config
from ..io.storage import DEFAULT_ROOT, StoragePaths, today_iso
from .admin_panel import router as admin_router
from .kite_api import router as kite_router


app = FastAPI(title="Abraxas Local UI", version="0.2.0")
app.include_router(kite_router)
app.include_router(admin_router)


def _paths(root: Optional[str]) -> StoragePaths:
    return StoragePaths(root=Path(root).expanduser() if root else DEFAULT_ROOT)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/oracle/{day}", response_class=JSONResponse)
def oracle_readout(day: str, root: Optional[str] = None):
    paths = _paths(root)
    p = paths.oracle_readout_path(day)
    if not p.exists():
        raise HTTPException(404, f"missing oracle.readout.json for {day}")
    return JSONResponse(content=p.read_text(encoding="utf-8"))


@app.get("/oracle/{day}/md", response_class=PlainTextResponse)
def oracle_md(day: str, root: Optional[str] = None):
    paths = _paths(root)
    _ = load_user_config(paths)
    p = paths.oracle_md_path(day)
    if not p.exists():
        raise HTTPException(404, f"missing oracle.md for {day}")
    return PlainTextResponse(content=p.read_text(encoding="utf-8"))


@app.get("/oracle/today/md", response_class=PlainTextResponse)
def oracle_today_md(root: Optional[str] = None):
    return oracle_md(today_iso(), root=root)
