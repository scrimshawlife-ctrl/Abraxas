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


def _fail_closed(reason: str) -> dict[str, Any]:
    payload = {
        "schema_version": "SelfBuildBatchTrends.v1",
        "status": "NOT_COMPUTABLE",
        "reason": reason,
        "cycle_count": 0,
        "latest_status": "NOT_COMPUTABLE",
        "counts_by_status": {},
        "approval_wait_ratio": 0.0,
        "apply_success_ratio": 0.0,
        "post_validation_pass_ratio": 0.0,
        "score_feedback_hashes": [],
        "flagged_trends": [f"FAIL_CLOSED:{reason}"],
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _sha256_text(_canonical(payload))
    return payload


def run_self_build_batch_trends() -> dict[str, Any]:
    if not LEDGER_PATH.exists():
        return _fail_closed("MISSING_LEDGER")

    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        ledger = json.load(handle)

    if not isinstance(ledger, dict) or ledger.get("schema_version") != "SelfBuildBatchLedger.v1":
        return _fail_closed("INVALID_LEDGER_SCHEMA")

    entries = ledger.get("entries")
    if not isinstance(entries, list) or not entries:
        return _fail_closed("EMPTY_LEDGER")

    counts_by_status: dict[str, int] = {}
    approval_wait_count = 0
    apply_success_count = 0
    post_validation_pass_count = 0
    score_hashes: list[str] = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status", "UNKNOWN"))
        counts_by_status[status] = counts_by_status.get(status, 0) + 1

        if status == "WAITING_FOR_APPROVAL":
            approval_wait_count += 1
        if status == "COMPLETE":
            apply_success_count += 1

        post = entry.get("post_validation", {}) if isinstance(entry.get("post_validation"), dict) else {}
        if post.get("validator") == "PASS" and post.get("operator_health") == "GREEN" and bool(post.get("invariance")):
            post_validation_pass_count += 1

        sf = entry.get("score_feedback", {}) if isinstance(entry.get("score_feedback"), dict) else {}
        sf_hash = sf.get("canonical_hash")
        if isinstance(sf_hash, str) and sf_hash:
            score_hashes.append(sf_hash)

    cycle_count = len(entries)
    latest = entries[-1] if isinstance(entries[-1], dict) else {}
    latest_status = str(latest.get("status", "UNKNOWN"))

    approval_wait_ratio = approval_wait_count / cycle_count
    apply_success_ratio = apply_success_count / cycle_count
    post_validation_pass_ratio = post_validation_pass_count / cycle_count

    flagged_trends: list[str] = []
    if approval_wait_ratio > 0.8:
        flagged_trends.append("HIGH_APPROVAL_WAIT_RATIO")
    if apply_success_ratio < 0.2:
        flagged_trends.append("LOW_APPLY_SUCCESS_RATIO")
    if post_validation_pass_ratio < 0.5:
        flagged_trends.append("LOW_POST_VALIDATION_PASS_RATIO")
    if len(set(score_hashes)) > 1:
        flagged_trends.append("SCORE_FEEDBACK_HASH_DRIFT")

    payload = {
        "schema_version": "SelfBuildBatchTrends.v1",
        "status": "OK",
        "cycle_count": cycle_count,
        "latest_status": latest_status,
        "counts_by_status": dict(sorted(counts_by_status.items(), key=lambda kv: kv[0])),
        "approval_wait_ratio": approval_wait_ratio,
        "apply_success_ratio": apply_success_ratio,
        "post_validation_pass_ratio": post_validation_pass_ratio,
        "score_feedback_hashes": sorted(set(score_hashes)),
        "flagged_trends": sorted(flagged_trends),
        "authority": {"mutation": False, "promotion": False, "execution": False, "analysis_only": True},
    }
    payload["canonical_hash"] = _sha256_text(_canonical(payload))
    return payload
