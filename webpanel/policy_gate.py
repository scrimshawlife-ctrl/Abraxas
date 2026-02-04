from __future__ import annotations

from typing import Any, Dict, Optional


class PolicyAckRequired(RuntimeError):
    pass


def _hash_prefix(value: Optional[str], length: int = 8) -> Optional[str]:
    if not value:
        return None
    return value[:length]


def policy_ack_required(run: Any, current_policy_hash: Optional[str]) -> bool:
    ingest_hash = getattr(run, "policy_hash_at_ingest", None)
    if not ingest_hash or not current_policy_hash:
        return False
    if ingest_hash == current_policy_hash:
        return False
    return not bool(getattr(run, "policy_ack", False))


def enforce_policy_ack(run: Any, current_policy_hash: Optional[str]) -> None:
    if policy_ack_required(run, current_policy_hash):
        raise PolicyAckRequired("policy_ack_required")


def record_policy_ack(
    *,
    run: Any,
    current_policy_hash: Optional[str],
    ledger,
    event_id: str,
    timestamp_utc: str,
) -> Dict[str, Any]:
    ingest_hash = getattr(run, "policy_hash_at_ingest", None)
    run.policy_ack = True
    data = {
        "ingest_policy_hash_prefix": _hash_prefix(ingest_hash),
        "current_policy_hash_prefix": _hash_prefix(current_policy_hash),
        "timestamp_utc": timestamp_utc,
    }
    ledger.append(run.run_id, event_id, "policy_ack", timestamp_utc, data)
    return data
