from __future__ import annotations

from typing import Any, Dict, Optional


class AgencyGateError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _hash_prefix(value: Optional[str], length: int = 8) -> Optional[str]:
    if not value:
        return None
    return value[:length]


def enable_agency(
    *,
    run: Any,
    mode: str,
    timestamp_utc: str,
    ledger,
    event_id: str,
    policy_hash: Optional[str],
) -> Dict[str, Any]:
    run.agency_enabled = True
    run.agency_mode = mode
    run.agency_enabled_utc = timestamp_utc
    run.agency_disabled_utc = None
    run.agency_disable_reason = None
    data = {
        "mode": mode,
        "timestamp_utc": timestamp_utc,
        "session_id": getattr(run, "session_id", None),
        "policy_hash_prefix": _hash_prefix(policy_hash),
    }
    ledger.append(run.run_id, event_id, "agency_enable", timestamp_utc, data)
    return data


def disable_agency(
    *,
    run: Any,
    reason: str,
    timestamp_utc: str,
    ledger,
    event_id: str,
) -> Dict[str, Any]:
    run.agency_enabled = False
    run.agency_mode = "off"
    run.agency_disabled_utc = timestamp_utc
    run.agency_disable_reason = reason
    data = {"reason": reason, "timestamp_utc": timestamp_utc}
    ledger.append(run.run_id, event_id, "agency_disable", timestamp_utc, data)
    return data


def enforce_agency_enabled(run: Any) -> None:
    if not bool(getattr(run, "agency_enabled", False)):
        raise AgencyGateError("agency_off")


def policy_changed(run: Any, current_policy_hash: Optional[str]) -> bool:
    ingest_hash = getattr(run, "policy_hash_at_ingest", None)
    return bool(ingest_hash and current_policy_hash and ingest_hash != current_policy_hash)


def auto_disable_on_policy_change(
    *,
    run: Any,
    current_policy_hash: Optional[str],
    ledger,
    event_id: str,
    timestamp_utc: str,
) -> bool:
    if not bool(getattr(run, "agency_enabled", False)):
        return False
    if not policy_changed(run, current_policy_hash):
        return False
    disable_agency(
        run=run,
        reason="policy_change",
        timestamp_utc=timestamp_utc,
        ledger=ledger,
        event_id=event_id,
    )
    return True

