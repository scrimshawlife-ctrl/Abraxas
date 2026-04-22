from __future__ import annotations

import os
from datetime import datetime, timezone

DEFAULT_MAX_AGE_SECONDS: dict[str, int] = {
    "developer_readiness": 300,
    "invariance": 300,
    "comparison": 300,
    "preflight": 300,
    "reporting_cycle": 300,
}


def _parse_utc(ts: str) -> datetime:
    normalized = ts.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)


def resolve_max_age_seconds(artifact_type: str) -> int:
    env_value = os.getenv("ABRAXAS_REPORT_MAX_AGE_SECONDS", "").strip()
    if env_value:
        try:
            parsed = int(env_value)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
    return int(DEFAULT_MAX_AGE_SECONDS.get(artifact_type, 300))


def evaluate_freshness(timestamp_utc: str | None, now_utc: str, *, artifact_type: str) -> dict[str, int | bool | str]:
    max_age = resolve_max_age_seconds(artifact_type)
    if not timestamp_utc:
        return {
            "status": "NOT_COMPUTABLE",
            "reason": "missing_timestamp",
            "is_stale": True,
            "age_seconds": -1,
            "max_age_seconds": max_age,
        }
    try:
        ts = _parse_utc(str(timestamp_utc))
        now = _parse_utc(now_utc)
    except ValueError:
        return {
            "status": "NOT_COMPUTABLE",
            "reason": "invalid_timestamp",
            "is_stale": True,
            "age_seconds": -1,
            "max_age_seconds": max_age,
        }
    age_seconds = max(0, int((now - ts).total_seconds()))
    return {
        "status": "OK",
        "reason": "ok",
        "is_stale": age_seconds > max_age,
        "age_seconds": age_seconds,
        "max_age_seconds": max_age,
    }
