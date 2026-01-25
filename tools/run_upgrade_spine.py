#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.abraxas.upgrade_spine.ledger import UpgradeSpineLedger
from server.abraxas.upgrade_spine.types import UpgradeCandidate, UpgradeDecision
from server.abraxas.upgrade_spine.upgrade_manager import (
    apply_candidate,
    cleanup_sandbox,
    collect_candidates,
    evaluate_candidate,
    finalize_artifact_bundle,
    promote_from_bundle,
    run_gates,
)
from server.abraxas.upgrade_spine.utils import compute_candidate_id, sort_candidates, utc_now_iso


def _load_candidate(ledger: UpgradeSpineLedger, candidate_id: str) -> UpgradeCandidate:
    entry = ledger.latest_entry("candidate", candidate_id)
    if not entry:
        raise ValueError(f"Candidate not found in ledger: {candidate_id}")
    payload = entry["payload"]
    return UpgradeCandidate(**payload)


def _load_decision(ledger: UpgradeSpineLedger, candidate_id: str) -> UpgradeDecision | None:
    entry = ledger.latest_entry("decision", candidate_id)
    if not entry:
        return None
    return UpgradeDecision(**entry["payload"])


def _load_bundle_entry(ledger: UpgradeSpineLedger, candidate_id: str) -> dict | None:
    entry = ledger.latest_bundle(candidate_id)
    if not entry:
        return None
    return entry["payload"]


def _print_json(obj: object) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade Spine v1 CLI")
    parser.add_argument("--collect", action="store_true", help="Collect upgrade candidates")
    parser.add_argument("--evaluate", type=str, help="Evaluate a candidate by ID")
    parser.add_argument("--apply", type=str, help="Apply a candidate by ID (sandbox + gates)")
    parser.add_argument("--promote", type=str, help="Promote a candidate by ID")
    args = parser.parse_args()

    ledger = UpgradeSpineLedger(ROOT)

    if args.collect:
        candidates = sort_candidates(collect_candidates(ROOT))
        for candidate in candidates:
            ledger.append("candidate", candidate.to_dict())
        _print_json([candidate.to_dict() for candidate in candidates])
        return

    if args.evaluate:
        candidate = _load_candidate(ledger, args.evaluate)
        decision = evaluate_candidate(candidate)
        ledger.append("decision", decision.to_dict())
        _print_json(decision.to_dict())
        return

    if args.apply:
        candidate = _load_candidate(ledger, args.apply)
        if not ledger.latest_entry("candidate", candidate.candidate_id):
            ledger.append("candidate", candidate.to_dict())
        try:
            artifact, bundle = apply_candidate(candidate, ROOT)
        except Exception as exc:
            decision_payload = {
                "candidate_id": candidate.candidate_id,
                "status": "archive",
                "reasons": [str(exc)],
                "not_computable": {
                    "status": "NOT_COMPUTABLE",
                    "reason": str(exc),
                    "missing_inputs": [],
                    "provenance": {"stage": "apply_candidate"},
                },
            }
            decision = UpgradeDecision(
                version="upgrade_decision.v0",
                run_id=candidate.run_id,
                created_at=utc_now_iso(),
                input_hash=compute_candidate_id(decision_payload),
                candidate_id=candidate.candidate_id,
                decision_id=compute_candidate_id(decision_payload),
                status="archive",
                reasons=[str(exc)],
                gate_report=None,
                not_computable=decision_payload["not_computable"],
            )
            ledger.append("decision", decision.to_dict())
            _print_json(decision.to_dict())
            return
        try:
            gate_report = run_gates(bundle, candidate, artifact.sandbox_root, ROOT).to_dict()
            status = "promote" if gate_report["overall_ok"] else "archive"
            decision_payload = {
                "candidate_id": candidate.candidate_id,
                "status": status,
                "reasons": [] if status == "promote" else ["gates_failed"],
                "gate_report": gate_report,
            }
            decision = UpgradeDecision(
                version="upgrade_decision.v0",
                run_id=candidate.run_id,
                created_at=utc_now_iso(),
                input_hash=compute_candidate_id(decision_payload),
                candidate_id=candidate.candidate_id,
                decision_id=compute_candidate_id(decision_payload),
                status=status,
                reasons=[] if status == "promote" else ["gates_failed"],
                gate_report=gate_report,
                not_computable=None,
            )
            bundle_dict = bundle.to_dict()
            bundle_dict["gate_report"] = gate_report
            bundle_dict["decision_id"] = decision.decision_id
            provenance_path = Path(bundle_dict["artifact_dir"]) / "provenance.json"
            provenance_path.write_text(
                json.dumps(bundle_dict, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            gate_path = Path(bundle_dict["artifact_dir"]) / "gate_report.json"
            gate_path.write_text(
                json.dumps(gate_report, indent=2, sort_keys=True),
                encoding="utf-8",
            )
            decision_path = Path(bundle_dict["artifact_dir"]) / "decision.json"
            decision_path.write_text(
                json.dumps(decision.to_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
            bundle_dict = finalize_artifact_bundle(Path(bundle_dict["artifact_dir"]), bundle_dict)
            ledger.append("decision", decision.to_dict())
            ledger.append("provenance_bundle", bundle_dict)
            _print_json({"decision": decision.to_dict(), "gate_report": gate_report})
        finally:
            cleanup_sandbox(artifact, ROOT)
        return

    if args.promote:
        candidate_id = args.promote
        decision = _load_decision(ledger, candidate_id)
        if not decision:
            raise ValueError(f"No decision found for candidate: {candidate_id}")
        bundle_entry = _load_bundle_entry(ledger, candidate_id)
        if not bundle_entry:
            raise ValueError(f"No provenance bundle found for candidate: {candidate_id}")
        artifact_dir = Path(bundle_entry["artifact_dir"])
        receipt = promote_from_bundle(decision, artifact_dir, ROOT)
        _print_json({"receipt": receipt})
        return

    parser.print_help()


if __name__ == "__main__":
    main()
