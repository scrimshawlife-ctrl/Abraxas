from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from .familiar_adapter import FamiliarAdapter
from .ledger import LedgerChain
from .store import InMemoryStore

templates = Jinja2Templates(directory="webpanel/templates")

store = InMemoryStore()
ledger = LedgerChain()
adapter = FamiliarAdapter()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def eid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


def _panel_token() -> str:
    return os.environ.get("ABX_PANEL_TOKEN", "").strip()


def _panel_host() -> str:
    return os.environ.get("ABX_PANEL_HOST", "127.0.0.1").strip() or "127.0.0.1"


def _panel_port() -> str:
    return os.environ.get("ABX_PANEL_PORT", "8008").strip() or "8008"


def _token_enabled() -> bool:
    return bool(_panel_token())


def require_token(request: Optional[Request], form: Optional[Mapping[str, Any]] = None) -> None:
    token = _panel_token()
    if not token:
        return
    if request is None:
        raise HTTPException(status_code=401, detail="invalid token")
    header_token = request.headers.get("X-ABX-Token")
    if header_token == token:
        return
    if form is not None and form.get("abx_token") == token:
        return
    raise HTTPException(status_code=401, detail="invalid token")
