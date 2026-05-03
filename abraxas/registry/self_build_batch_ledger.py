from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

LEDGER_PATH = Path("out/registry/self_build_batch_ledger.latest.json")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _load_ledger() -> dict[str, Any]:
    if not LEDGER_PATH.exists():
        return {
            "schema_version": "SelfBuildBatchLedger.v1",
            "entry_count": 0,
            "entries": [],
            "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
            "canonical_hash": None,
        }
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    return loaded if isinstance(loaded, dict) else _load_ledger()


def build_batch_entry(batch_cycle: dict[str, Any]) -> dict[str, Any]:
    approvals = 0
    for phase in batch_cycle.get("phase_results", []):
        if isinstance(phase, dict) and phase.get("phase") == "APPROVAL":
            approvals = int(phase.get("approved_count", 0))
            break

    applied_count = 0
    for phase in batch_cycle.get("phase_results", []):
        if isinstance(phase, dict) and phase.get("phase") == "APPLY":
            applied_count = int(phase.get("applied_count", 0))
            break

    score_feedback = batch_cycle.get("score_feedback", {}) if isinstance(batch_cycle.get("score_feedback"), dict) else {}
    basis = _canonical(
        {
            "status": batch_cycle.get("status"),
            "batch_hash": batch_cycle.get("canonical_hash"),
            "approvals": approvals,
            "applied_count": applied_count,
            "score_feedback_hash": score_feedback.get("canonical_hash"),
        }
    )
    cycle_id = "cycle-" + _sha256_text(basis)[:20]

    return {
        "cycle_id": cycle_id,
        "status": batch_cycle.get("status", "NOT_COMPUTABLE"),
        "approvals": approvals,
        "applied_count": applied_count,
        "score_feedback": {
            "status": score_feedback.get("status", "NOT_RUN"),
            "ranked_count": score_feedback.get("ranked_count", 0),
            "flagged_count": score_feedback.get("flagged_count", 0),
            "blocked_count": score_feedback.get("blocked_count", 0),
            "canonical_hash": score_feedback.get("canonical_hash"),
        },
        "batch_cycle_hash": batch_cycle.get("canonical_hash"),
        "post_validation": batch_cycle.get("post_validation", {}),
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }


def append_batch_entry(batch_cycle: dict[str, Any]) -> dict[str, Any]:
    ledger = _load_ledger()
    entry = build_batch_entry(batch_cycle)
    entries = ledger.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    entries.append(entry)
    payload = {
        "schema_version": "SelfBuildBatchLedger.v1",
        "entry_count": len(entries),
        "entries": entries,
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _sha256_text(_canonical(payload))
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEDGER_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload
