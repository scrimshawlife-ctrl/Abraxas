from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from abraxas.canary.closure_ledger_models import AUTHORITY_FLAGS
from abraxas.core.canonical import canonical_json


def _sha(obj: Any) -> str:
    return sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def build_cycle_closure_ledger(
    report: Mapping[str, Any],
    previous: Mapping[str, Any] | None = None,
) -> dict:
    report_obj = deepcopy(dict(report))
    prior_obj = deepcopy(dict(previous)) if previous is not None else {}

    prior_entries = prior_obj.get("entries") if isinstance(prior_obj.get("entries"), list) else []
    prior_by_id = {str(e.get("entry_id")): e for e in prior_entries if isinstance(e, dict) and e.get("entry_id")}

    report_id = report_obj.get("report_id")
    report_hash = report_obj.get("report_hash")
    entry_id = _sha({"report_id": report_id, "report_hash": report_hash})

    created = 0
    existing = 0
    entries = list(prior_by_id.values())

    if entry_id in prior_by_id:
        existing = 1
    else:
        created = 1
        lineage_hash = _sha({"report_id": report_id, "report_hash": report_hash, "lineage": report_obj.get("lineage")})
        entries.append(
            {
                "entry_version": "CanaryCycleClosureLedgerEntry.v1",
                "entry_id": entry_id,
                "report_id": report_id,
                "report_hash": report_hash,
                "closure_status": report_obj.get("closure", {}).get("closure_status"),
                "closure_reason": report_obj.get("closure", {}).get("reason"),
                "observation_symmetry_status": report_obj.get("symmetry", {}).get("observation_symmetry_status"),
                "reversibility_status": report_obj.get("reversibility", {}).get("reversibility_status"),
                "report_snapshot": report_obj,
                "audit": {
                    "report_hash": report_hash,
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

    entries = sorted(entries, key=lambda e: (str(e.get("closure_status", "")), str(e.get("report_id", "")), str(e.get("entry_id", ""))))

    counts = {
        "reports_total": 1,
        "entries_created": created,
        "entries_existing": existing,
        "entries_total": len(entries),
        "closed": sum(1 for e in entries if e.get("closure_status") == "closed"),
        "open": sum(1 for e in entries if e.get("closure_status") == "open"),
        "not_computable": sum(1 for e in entries if e.get("closure_status") == "not_computable"),
    }

    return {
        "artifact": "CANARY-CYCLE-CLOSURE-LEDGER-001",
        "schema_version": "CanaryCycleClosureLedgerRun.v1",
        "authority": dict(AUTHORITY_FLAGS),
        "counts": counts,
        "entries": entries,
    }
