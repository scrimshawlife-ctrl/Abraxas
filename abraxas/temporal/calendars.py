"""Calendar event catalog (scaffold only)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def list_calendars() -> List[str]:
    return ["gregorian", "iso_week"]


def events_in_window(window_utc: Dict[str, str], calendars: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    return []
