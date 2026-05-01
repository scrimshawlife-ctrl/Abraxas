from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.trend_ledger_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_trend_ledger(
    analysis: Mapping[str, Any],
    previous: Mapping[str, Any] | None = None,
) -> dict:
    analysis_obj = deepcopy(dict(analysis))
    prior_obj = deepcopy(dict(previous)) if previous is not None else {}

    prior_entries = prior_obj.get("entries") if isinstance(prior_obj.get("entries"), list) else []
    prior_by_id = {str(e.get("entry_id")): e for e in prior_entries if isinstance(e, dict) and e.get("entry_id")}

    analysis_id = analysis_obj.get("analysis_id")
    analysis_hash = analysis_obj.get("analysis_hash")
    entry_id = _sha({"analysis_id": analysis_id, "analysis_hash": analysis_hash})

    created = 0
    existing = 0
    entries = list(prior_by_id.values())

    if entry_id in prior_by_id:
        existing = 1
    else:
        created = 1
        lineage_hash = _sha(
            {
                "analysis_id": analysis_id,
                "analysis_hash": analysis_hash,
                "lineage": analysis_obj.get("lineage"),
            }
        )
        entries.append(
            {
                "entry_version": "CanaryTrendLedgerEntry.v1",
                "entry_id": entry_id,
                "analysis_id": analysis_id,
                "analysis_hash": analysis_hash,
                "trend_status": analysis_obj.get("trend", {}).get("status"),
                "trend_reason": analysis_obj.get("trend", {}).get("reason"),
                "rates": deepcopy(analysis_obj.get("rates", {})),
                "counts": deepcopy(analysis_obj.get("counts", {})),
                "analysis_snapshot": analysis_obj,
                "audit": {
                    "analysis_hash": analysis_hash,
                    "lineage_hash": lineage_hash,
                },
                "review": {
                    "ledger_status": "recorded",
                    "review_notes": [],
                    "decision_reason": None,
                },
                "authority": dict(AUTHORITY_FLAGS),
            }
        )

    entries = sorted(entries, key=lambda e: (str(e.get("trend_status", "")), str(e.get("analysis_id", "")), str(e.get("entry_id", ""))))

    counts = {
        "analyses_total": 1,
        "entries_created": created,
        "entries_existing": existing,
        "entries_total": len(entries),
        "stable": sum(1 for e in entries if e.get("trend_status") == "stable"),
        "needs_attention": sum(1 for e in entries if e.get("trend_status") == "needs_attention"),
        "not_computable": sum(1 for e in entries if e.get("trend_status") == "not_computable"),
    }

    return {
        "artifact": "CANARY-TREND-LEDGER-001",
        "schema_version": "CanaryTrendLedgerRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": counts,
        "entries": entries,
    }
