from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class DiffResult:
    reason: str
    meta: Dict[str, Any]


def diff_hashes(
    *,
    prior_run_id: Optional[str],
    current_run_id: Optional[str],
    prior_hash: Optional[str],
    current_hash: Optional[str],
    meta: Dict[str, Any],
) -> DiffResult:
    if prior_hash is None and current_hash is None:
        reason = "both_missing"
    elif prior_hash is None:
        reason = "prior_missing"
    elif current_hash is None:
        reason = "current_missing"
    elif prior_hash == current_hash:
        reason = "hash_equal"
    else:
        reason = "hash_mismatch"
    return DiffResult(reason=reason, meta={
        "prior_run_id": prior_run_id,
        "current_run_id": current_run_id,
        **meta,
    })
