from __future__ import annotations

import secrets
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Optional

from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from .familiar_adapter import FamiliarAdapter
from .ledger import LedgerChain
from .store import InMemoryStore

_templates_env: Optional[Jinja2Templates] = None


def templates_factory() -> Jinja2Templates:
    global _templates_env
    if _templates_env is None:
        try:
            import jinja2  # noqa: F401
        except ImportError:
            raise ImportError(
                "Missing dependency: jinja2. Install Abraxas with webpanel extras: "
                "pip install 'abraxas[webpanel]'"
            )
        _templates_env = Jinja2Templates(directory="webpanel/templates")
    return _templates_env


# Lazy accessor for backwards compat
templates = None  # type: ignore[assignment]


class _LazyTemplates:
    def __getattr__(self, name: str):  # type: ignore[override]
        return getattr(templates_factory(), name)


templates = _LazyTemplates()  # type: ignore[assignment]

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


# Hosts that are only reachable from this machine. The whole 127.0.0.0/8 block is
# loopback, not just 127.0.0.1, and ::1 is its IPv6 equivalent. "localhost" is kept as
# a name because uvicorn accepts it and it is what a user is most likely to type.
_LOOPBACK_NAMES = frozenset({"localhost", "::1", "[::1]", ""})


def _is_loopback_host(host: str) -> bool:
    """True when binding this host cannot be reached from another machine."""
    candidate = (host or "").strip()
    if candidate in _LOOPBACK_NAMES:
        return True
    try:
        import ipaddress

        return ipaddress.ip_address(candidate).is_loopback
    except ValueError:
        return False


def ensure_bind_is_safe(host: str) -> None:
    """Refuse to bind a non-loopback host unless a token is configured.

    The default posture was already correct -- loopback unless ABX_PANEL_HOST says
    otherwise -- but the LAN opt-in and the token were independent: setting
    ABX_PANEL_HOST=0.0.0.0 without ABX_PANEL_TOKEN published every mutating route with
    no credential. A banner warned about it; a warning is not a control.

    Loopback with no token still works, deliberately: this guard must not break the
    default case. Only the combination is refused.
    """
    if _is_loopback_host(host):
        return
    if _panel_token():
        return
    raise RuntimeError(
        f"refusing to bind non-loopback host {host!r} without ABX_PANEL_TOKEN set. "
        "Set ABX_PANEL_TOKEN to a secret, or bind 127.0.0.1. "
        "Exposing the panel on the network makes every state-changing route reachable "
        "without a credential."
    )


def require_token(request: Optional[Request], form: Optional[Mapping[str, Any]] = None) -> None:
    token = _panel_token()
    if not token:
        return
    if request is None:
        raise HTTPException(status_code=401, detail="invalid token")
    header_token = request.headers.get("X-ABX-Token")
    # compare_digest, not ==: a short-circuiting comparison leaks how many leading
    # characters were guessed correctly through timing.
    if isinstance(header_token, str) and secrets.compare_digest(header_token, token):
        return
    form_token = form.get("abx_token") if form is not None else None
    if isinstance(form_token, str) and secrets.compare_digest(form_token, token):
        return
    raise HTTPException(status_code=401, detail="invalid token")
