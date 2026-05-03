from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from abraxas.operator.closure_card import run_operator_closure_card

from .binding_validator import run_binding_validator
from .invariance_harness import run_invariance_harness
from .self_build_approval_input import load_self_build_approval_input
from .self_build_mutation_ledger import append_mutation_entry, build_mutation_entry, snapshot_before_content
from .self_build_operator_queue import run_self_build_operator_queue
from .self_build_patch_plan import run_self_build_patch_plan


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    if not path.exists():
        return "NOT_FOUND"
    return _sha256_text(path.read_text(encoding="utf-8"))


def _write_computable_artifact(path: Path) -> tuple[str, str, dict[str, str]]:
    before_hash = _file_hash(path)
    before_content = path.read_text(encoding="utf-8") if path.exists() else "{}"
    before_snapshot = snapshot_before_content(before_content)

    existing: dict[str, Any] = {}
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except Exception:
            existing = {}

    payload = {
        "schema_version": existing.get("schema_version", "UnknownSchema.v1"),
        "status": "COMPUTABLE",
        "upgraded_from": existing.get("status", "UNKNOWN"),
        "deterministic": True,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    after_hash = _file_hash(path)
    return before_hash, after_hash, before_snapshot


def _fail_result(status: str, approved_count: int, results: list[dict[str, Any]], post_validation: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "schema_version": "SelfBuildMultiApplyResult.v1",
        "status": status,
        "approved_count": approved_count,
        "applied_count": 0,
        "results": results,
        "post_validation": post_validation,
        "mutation_ledger": {"entry_count": 0, "canonical_hash": None},
        "authority": {
            "mutation": True,
            "promotion": False,
            "execution": False,
            "artifact_only": True,
            "operator_approval_required": True,
            "fail_closed": True,
        },
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload


def run_self_build_multi_apply() -> dict[str, Any]:
    approval_input = load_self_build_approval_input()
    approved_ids = sorted(approval_input["approved_ids"])

    if not approved_ids:
        return _fail_result(
            status="NO_APPROVED_ITEMS",
            approved_count=0,
            results=[{"code": "NO_APPROVED_IDS", "message": "No approved ids present in approval input"}],
            post_validation={"validator": "NOT_RUN", "operator_health": "NOT_RUN", "invariance": False},
        )

    queue = run_self_build_operator_queue()
    queue_by_id = {item["approval_id"]: item for item in queue["items"]}

    unknown_ids = [approval_id for approval_id in approved_ids if approval_id not in queue_by_id]
    if unknown_ids:
        return _fail_result(
            status="NOT_COMPUTABLE",
            approved_count=len(approved_ids),
            results=[{"code": "UNKNOWN_APPROVAL_ID", "ids": unknown_ids}],
            post_validation={"validator": "NOT_RUN", "operator_health": "NOT_RUN", "invariance": False},
        )

    approved_items = [queue_by_id[approval_id] for approval_id in approved_ids]
    targets = [item["target_path"] for item in approved_items]

    if any(not target.startswith("out/") for target in targets):
        return _fail_result(
            status="NOT_COMPUTABLE",
            approved_count=len(approved_ids),
            results=[{"code": "TARGET_OUTSIDE_OUT", "targets": sorted(targets)}],
            post_validation={"validator": "NOT_RUN", "operator_health": "NOT_RUN", "invariance": False},
        )

    if len(set(targets)) != len(targets):
        return _fail_result(
            status="NOT_COMPUTABLE",
            approved_count=len(approved_ids),
            results=[{"code": "DUPLICATE_TARGET_PATH", "targets": sorted(targets)}],
            post_validation={"validator": "NOT_RUN", "operator_health": "NOT_RUN", "invariance": False},
        )

    patch_plan = run_self_build_patch_plan()
    plan_by_target = {plan["target_path"]: plan for plan in patch_plan["plans"]}

    applied_results = []
    ledger_payload: dict[str, Any] | None = None
    for item in sorted(approved_items, key=lambda entry: (entry["target_path"], entry["approval_id"])):
        target_path = item["target_path"]
        target = Path(target_path)
        before_hash, after_hash, before_snapshot = _write_computable_artifact(target)

        entry = build_mutation_entry(
            approval_id=item["approval_id"],
            target_path=target_path,
            before_hash=before_hash,
            after_hash=after_hash,
            before_snapshot=before_snapshot,
            post_validation={"validator": "PENDING", "operator_card": "PENDING", "invariance": False},
        )
        ledger_payload = append_mutation_entry(entry)

        applied_results.append(
            {
                "approval_id": item["approval_id"],
                "target_path": target_path,
                "applied": True,
                "validation_commands": plan_by_target.get(target_path, {}).get("validation_commands", []),
            }
        )

    validator = run_binding_validator()
    operator = run_operator_closure_card()
    invariance_run = run_invariance_harness()
    invariance_ok = (
        invariance_run["registry_invariant"]
        and invariance_run["validator_invariant"]
        and invariance_run["bundle_invariant"]
    )

    post_validation = {
        "validator": validator["overall_status"],
        "operator_health": operator["health"],
        "invariance": invariance_ok,
    }

    if validator["overall_status"] != "PASS" or operator["health"] != "GREEN" or not invariance_ok:
        return _fail_result(
            status="NOT_COMPUTABLE",
            approved_count=len(approved_ids),
            results=applied_results,
            post_validation=post_validation,
        )

    payload = {
        "schema_version": "SelfBuildMultiApplyResult.v1",
        "status": "APPLIED",
        "approved_count": len(approved_ids),
        "applied_count": len(applied_results),
        "results": applied_results,
        "post_validation": post_validation,
        "mutation_ledger": {
            "entry_count": 0 if ledger_payload is None else ledger_payload["entry_count"],
            "canonical_hash": None if ledger_payload is None else ledger_payload["canonical_hash"],
        },
        "authority": {
            "mutation": True,
            "promotion": False,
            "execution": False,
            "artifact_only": True,
            "operator_approval_required": True,
            "fail_closed": True,
        },
    }
    payload["canonical_hash"] = _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return payload
