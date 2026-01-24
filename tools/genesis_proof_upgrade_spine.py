#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.abraxas.upgrade_spine.ledger import UpgradeSpineLedger
from server.abraxas.upgrade_spine.types import UpgradeCandidate, UpgradeDecision
from server.abraxas.upgrade_spine.upgrade_manager import (
    apply_candidate,
    cleanup_sandbox,
    finalize_artifact_bundle,
    promote_from_bundle,
    run_gates,
)
from server.abraxas.upgrade_spine.utils import compute_candidate_id, sort_candidates, utc_now_iso


def _git_commit(root: Path) -> Optional[str]:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()
    except Exception:
        return None


def _write_receipt(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _select_safe_candidate(candidates: list[UpgradeCandidate]) -> Optional[UpgradeCandidate]:
    for candidate in candidates:
        if candidate.change_type == "docs_only" and candidate.not_computable is None:
            return candidate
    for candidate in candidates:
        if candidate.constraints.get("safe_canary") and candidate.not_computable is None:
            return candidate
    return None


def _load_ledger_candidates(ledger: UpgradeSpineLedger) -> list[UpgradeCandidate]:
    entries = [
        entry
        for entry in ledger.read_entries()
        if entry.get("entry_type") == "candidate"
    ]
    candidates = [UpgradeCandidate(**entry["payload"]) for entry in entries]
    return sort_candidates(candidates)


def run_genesis_proof(
    root: Path,
    gate_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ledger = UpgradeSpineLedger(root)
    candidates = _load_ledger_candidates(ledger)
    if not candidates:
        from server.abraxas.upgrade_spine.upgrade_manager import collect_candidates

        candidates = sort_candidates(collect_candidates(root))
        for candidate in candidates:
            ledger.append("candidate", candidate.to_dict())
    safe_candidate = _select_safe_candidate(candidates)
    run_date = utc_now_iso()[:10]
    receipt_path = root / ".aal" / "ledger" / "upgrade_spine" / "genesis" / run_date / "genesis_receipt.json"
    if not safe_candidate:
        refusal = {
            "status": "NOT_COMPUTABLE",
            "reason": "no_safe_candidate_found",
            "created_at": utc_now_iso(),
            "candidate_id": None,
            "decision_id": None,
            "artifact_dir": None,
            "patch_diff_hash": None,
            "overall_ok": False,
            "git_commit_before": _git_commit(root),
            "git_commit_after": _git_commit(root),
        }
        _write_receipt(receipt_path, refusal)
        return refusal

    artifact, bundle = apply_candidate(safe_candidate, root)
    try:
        gate_report = run_gates(
            bundle,
            safe_candidate,
            artifact.sandbox_root,
            root,
            gate_overrides=gate_overrides,
        ).to_dict()
        decision_payload = {
            "candidate_id": safe_candidate.candidate_id,
            "status": "promote" if gate_report["overall_ok"] else "archive",
            "reasons": [] if gate_report["overall_ok"] else ["gates_failed"],
            "gate_report": gate_report,
        }
        decision_id = compute_candidate_id(decision_payload)
        decision = UpgradeDecision(
            version="upgrade_decision.v0",
            run_id=safe_candidate.run_id,
            created_at=utc_now_iso(),
            input_hash=compute_candidate_id(decision_payload),
            candidate_id=safe_candidate.candidate_id,
            decision_id=decision_id,
            status=decision_payload["status"],
            reasons=decision_payload["reasons"],
            gate_report=gate_report,
            not_computable=None,
        )
        bundle_dict = bundle.to_dict()
        bundle_dict["gate_report"] = gate_report
        bundle_dict["decision_id"] = decision.decision_id
        bundle_dir = Path(bundle_dict["artifact_dir"])
        bundle_dir.joinpath("gate_report.json").write_text(
            json.dumps(gate_report, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        bundle_dir.joinpath("decision.json").write_text(
            json.dumps(decision.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        bundle_dir.joinpath("provenance.json").write_text(
            json.dumps(bundle_dict, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        bundle_dict = finalize_artifact_bundle(bundle_dir, bundle_dict)
        ledger.append("decision", decision.to_dict())
        ledger.append("provenance_bundle", bundle_dict)

        git_before = _git_commit(root)
        receipt: Dict[str, Any] = {
            "status": "OK" if gate_report["overall_ok"] else "NOT_PROMOTED",
            "created_at": utc_now_iso(),
            "candidate_id": safe_candidate.candidate_id,
            "decision_id": decision.decision_id,
            "artifact_dir": bundle_dict["artifact_dir"],
            "patch_diff_hash": bundle_dict.get("artifact_hashes", {}).get("patch.diff"),
            "overall_ok": gate_report["overall_ok"],
            "git_commit_before": git_before,
            "git_commit_after": git_before,
        }
        if gate_report["overall_ok"]:
            promote_from_bundle(decision, bundle_dir, root)
            receipt["git_commit_after"] = _git_commit(root)
        else:
            receipt["reason"] = "gates_failed"
        _write_receipt(receipt_path, receipt)
        return receipt
    finally:
        cleanup_sandbox(artifact, root)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genesis Proof runner for Upgrade Spine v1")
    parser.add_argument("--root", type=str, default=str(ROOT), help="Repo root")
    parser.add_argument("--gate-overrides", type=str, default=None, help="JSON string for gate overrides")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    gate_overrides = json.loads(args.gate_overrides) if args.gate_overrides else None
    receipt = run_genesis_proof(root, gate_overrides=gate_overrides)
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
