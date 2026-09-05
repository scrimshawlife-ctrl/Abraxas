"""Structured fail logs. Never emit secrets."""

from __future__ import annotations

import json
import logging
from typing import Any

LOGGER = logging.getLogger("abraxas.research_rag")

_REDACT_KEYS = frozenset({"token", "authorization", "notion_token", "api_key", "secret"})


def log_fail(event: str, **fields: Any) -> None:
    payload = {"event": event}
    for key, value in fields.items():
        if str(key).lower() in _REDACT_KEYS:
            continue
        payload[key] = value
    LOGGER.error("research_rag_fail %s", json.dumps(payload, sort_keys=True, default=str))
