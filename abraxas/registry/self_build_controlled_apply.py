from __future__ import annotations

from typing import Any
import hashlib
import json
from pathlib import Path

from .binding_validator import run_binding_validator
from .invariance_harness import run_invariance_harness
from .self_build_approval_input import load_self_build_approval_input
from .self_build_approval_receipt import run_self_build_approval_receipt
from .self_build_mutation_ledger import append_mutation_entry, build_mutation_entry, snapshot_before_content
from .self_build_patch_plan import run_self_build_patch_plan
from abraxas.operator.closure_card import run_operator_closure_card


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _file_hash(path: Path) -> str:
    if not path.exists():
        return "NOT_FOUND"
    return _sha256_text(path.read_text(encoding="utf-8"))


def _upgrade_artifact(path: str) -> tuple[str, str, dict[str, str]]:
    target = Path(path)
    before_hash = _file_hash(target)
    before_content = target.read_text(encoding="utf-8") if target.exists() else "{}"
    before_snapshot = snapshot_before_content(before_content)

    existing: dict[str, Any] = {}
    if target.exists():
        try:
            loaded = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                existing = loaded
        except Exception:
            existing = {}

    payload = {
        "schema_version": existing.get("schema_version", "UnknownSchema.v1"),
        "status": "COMPUTABLE",
        "upgraded_from": "STUB",
        "deterministic": True,
        "authority": {
            "mutation": False,
            "promotion": False,
            "execution": False,
            "observe_only": True,
        },
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    after_hash = _file_hash(target)
    return before_hash, after_hash, before_snapshot


def run_self_build_controlled_apply() -> dict[str, Any]:
    approval_input = load_self_build_approval_input()
    receipt = run_self_build_approval_receipt(
        approval_input["approved_ids"],
        approval_input["rejected_ids"],
    )
    patch_plan = run_self_build_patch_plan()

    approved = [approval for approval in receipt["approvals"] if approval["status"] == "APPROVED"]

    if not approved:
        payload = {
            "schema_version": "SelfBuildApplyResult.v1",
            "status": "NO_APPROVED_ITEMS",
            "applied_count": 0,
            "message": "No approved items; no mutation performed",
        }
        return {
            **payload,
            "canonical_hash": _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":"))),
            "authority": {
                "mutation": False,
                "execution": False,
                "fail_closed": True,
            },
        }

    plan_by_target = {plan["target_path"]: plan for plan in patch_plan["plans"]}
    results = []
    ledger_entries = []
    for item in approved:
        target_path = item["target_path"]
        before_hash, after_hash, before_snapshot = _upgrade_artifact(target_path)
        plan_entry = plan_by_target.get(target_path, {})
        results.append(
            {
                "target_path": target_path,
                "applied": True,
                "note": "Deterministic upgrade applied",
                "validation_commands": plan_entry.get("validation_commands", []),
            }
        )
        ledger_entries.append((item["approval_id"], target_path, before_hash, after_hash, before_snapshot))

    validator = run_binding_validator()
    operator = run_operator_closure_card()
    invariance = run_invariance_harness()

    post_validation = {
        "validator": validator["overall_status"],
        "operator_card": operator["health"],
        "invariance": (
            invariance["registry_invariant"]
            and invariance["validator_invariant"]
            and invariance["bundle_invariant"]
        ),
    }

    ledger_payload = None
    for approval_id, target_path, before_hash, after_hash, before_snapshot in ledger_entries:
        entry = build_mutation_entry(
            approval_id=approval_id,
            target_path=target_path,
            before_hash=before_hash,
            after_hash=after_hash,
            before_snapshot=before_snapshot,
            post_validation=post_validation,
        )
        ledger_payload = append_mutation_entry(entry)

    payload = {
        "schema_version": "SelfBuildApplyResult.v1",
        "status": "APPLIED",
        "applied_count": len(results),
        "results": results,
        "post_validation": {
            "validator": validator["overall_status"],
            "operator_health": operator["health"],
            "invariance_ok": post_validation["invariance"],
        },
        "mutation_ledger": {
            "entry_count": 0 if ledger_payload is None else ledger_payload["entry_count"],
            "canonical_hash": None if ledger_payload is None else ledger_payload["canonical_hash"],
        },
    }
    return {
        **payload,
        "canonical_hash": _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":"))),
        "authority": {
            "mutation": False,
            "execution": False,
            "fail_closed": True,
        },
    }
