from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from server.abraxas.upgrade_spine.adapters.drift_adapter import collect_drift_candidates
from server.abraxas.upgrade_spine.adapters.evogate_adapter import collect_evogate_candidates
from server.abraxas.upgrade_spine.adapters.rent_adapter import collect_rent_candidates
from server.abraxas.upgrade_spine.adapters.shadow_adapter import collect_shadow_candidates
from server.abraxas.upgrade_spine.ledger import UpgradeSpineLedger
from server.abraxas.upgrade_spine.types import UpgradeCandidate, UpgradeDecision
from server.abraxas.upgrade_spine.upgrade_manager import (
    apply_candidate,
    collect_candidates,
    finalize_artifact_bundle,
    promote_from_bundle,
    promote_or_archive,
    run_gates,
)
from server.abraxas.upgrade_spine.utils import compute_candidate_id, sort_candidates, utc_now_iso


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Upgrade Spine Tests"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    (root / "README.md").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=root,
        check=True,
        capture_output=True,
    )


def _make_candidate() -> UpgradeCandidate:
    patch_plan = {
        "format_version": "0.1",
        "operations": [
            {"op": "write_file", "path": "README.md", "content": "baseline\nupgrade\n"},
        ],
        "notes": ["test_write"],
    }
    payload = {
        "source_loop": "manual",
        "change_type": "docs_only",
        "target_paths": ["README.md"],
        "patch_plan": patch_plan,
        "evidence_refs": [],
        "constraints": {"no_direct_canon_write": True},
        "not_computable": None,
    }
    candidate_id = compute_candidate_id(payload)
    return UpgradeCandidate(
        version="upgrade_candidate.v0",
        run_id="test",
        created_at=utc_now_iso(),
        input_hash=compute_candidate_id(payload),
        candidate_id=candidate_id,
        source_loop="manual",
        change_type="docs_only",
        target_paths=["README.md"],
        patch_plan=patch_plan,
        evidence_refs=[],
        constraints={"no_direct_canon_write": True},
        not_computable=None,
    )


def test_collect_candidates_deterministic(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "out" / "reports" / "rent_check_20250101_000000.json",
        {"passed": True, "failures": [], "warnings": []},
    )
    _write_json(
        tmp_path / "out" / "drift_report_v1.json",
        {"schema_version": "1.0.0", "clusters": []},
    )
    outcomes_path = tmp_path / ".aal" / "ledger" / "outcomes.jsonl"
    outcomes_path.parent.mkdir(parents=True, exist_ok=True)
    outcomes_path.write_text(
        json.dumps(
            {
                "cycle": 1,
                "shadow_metrics": {"SEI": 0.1},
                "canonical_metrics": {"A": 1.0},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    evogate_path = tmp_path / "out" / "evogate_run.json"
    _write_json(
        evogate_path,
        {
            "run_id": "run",
            "ts": "2025-01-01T00:00:00Z",
            "pack_id": "pack",
            "applied_proposal_ids": ["p1"],
            "candidate_policy_path": "out/policies/candidate.json",
            "baseline_metrics_path": None,
            "replay": {"ok": True, "metric_deltas": {}, "notes": [], "provenance": {}},
            "promote_recommended": False,
            "thresholds": {},
            "notes": [],
            "provenance": {},
        },
    )
    _write_json(
        tmp_path / "data" / "evolution" / "candidates" / "cand_test_001.json",
        {
            "candidate_id": "cand_test_001",
            "kind": "param_tweak",
            "source_domain": "AALMANAC",
            "proposed_at": "2025-01-01T00:00:00Z",
            "proposed_by": "test",
            "name": "param",
            "description": "desc",
            "rationale": "rationale",
            "param_path": "path.to.param",
            "current_value": 1.0,
            "proposed_value": 2.0,
            "priority": 5,
        },
    )
    first = [c.to_dict() for c in collect_candidates(tmp_path)]
    second = [c.to_dict() for c in collect_candidates(tmp_path)]
    assert first == second


def test_adapters_missing_input_not_computable(tmp_path: Path) -> None:
    shadow = collect_shadow_candidates(tmp_path)[0]
    rent = collect_rent_candidates(tmp_path)[0]
    drift = collect_drift_candidates(tmp_path)[0]
    evogate = collect_evogate_candidates(tmp_path)[0]
    assert shadow.not_computable is not None
    assert rent.not_computable is not None
    assert drift.not_computable is not None
    assert evogate.not_computable is not None
    assert not list(tmp_path.rglob("*"))


def test_gate_enforcement_blocks_promotion(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    candidate = _make_candidate()
    artifact, bundle = apply_candidate(candidate, tmp_path)
    gate_report = run_gates(
        bundle,
        candidate,
        artifact.sandbox_root,
        tmp_path,
        gate_overrides={
            "schema_validation": {"ok": True, "message": None},
            "dozen_run_invariance": {"ok": False, "verdict": "FAIL"},
            "rent_enforcement": {"ok": True},
            "missing_input": {"ok": True},
        },
    )
    assert gate_report.overall_ok is False


def test_promotion_and_archive_lifecycle(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    candidate = _make_candidate()
    artifact, bundle = apply_candidate(candidate, tmp_path)
    gate_report = run_gates(
        bundle,
        candidate,
        artifact.sandbox_root,
        tmp_path,
        gate_overrides={
            "schema_validation": {"ok": True, "message": None},
            "dozen_run_invariance": {"ok": True, "verdict": "PASS"},
            "rent_enforcement": {"ok": True},
            "missing_input": {"ok": True},
        },
    )
    decision_payload = {
        "candidate_id": candidate.candidate_id,
        "status": "promote",
        "reasons": [],
        "gate_report": gate_report.to_dict(),
    }
    decision = UpgradeDecision(
        version="upgrade_decision.v0",
        run_id="test",
        created_at=utc_now_iso(),
        input_hash=compute_candidate_id(decision_payload),
        candidate_id=candidate.candidate_id,
        decision_id=compute_candidate_id(decision_payload),
        status="promote",
        reasons=[],
        gate_report=gate_report.to_dict(),
        not_computable=None,
    )
    bundle_dict = bundle.to_dict()
    bundle_dict["gate_report"] = gate_report.to_dict()
    bundle = bundle.__class__(**bundle_dict)
    receipt = promote_or_archive(decision, bundle, artifact, tmp_path)
    ledger = UpgradeSpineLedger(tmp_path)
    assert ledger.latest_entry("promotion", candidate.candidate_id) is not None
    bundle_root = tmp_path / ".aal" / "artifacts" / "upgrade_spine"
    assert receipt
    assert any(bundle_root.rglob("patch.diff"))
    assert "upgrade" in (tmp_path / "README.md").read_text(encoding="utf-8")

    archive_decision = UpgradeDecision(
        version="upgrade_decision.v0",
        run_id="test",
        created_at=utc_now_iso(),
        input_hash="archive",
        candidate_id=candidate.candidate_id,
        decision_id="archive",
        status="archive",
        reasons=["gates_failed"],
        gate_report=None,
        not_computable=None,
    )
    promote_or_archive(archive_decision, bundle, artifact, tmp_path)
    assert ledger.latest_entry("archive", candidate.candidate_id) is not None


def test_collect_persists_candidates(tmp_path: Path) -> None:
    _write_json(
        tmp_path / "out" / "reports" / "rent_check_20250101_000000.json",
        {"passed": True, "failures": [], "warnings": []},
    )
    _write_json(
        tmp_path / "out" / "drift_report_v1.json",
        {"schema_version": "1.0.0", "clusters": []},
    )
    outcomes_path = tmp_path / ".aal" / "ledger" / "outcomes.jsonl"
    outcomes_path.parent.mkdir(parents=True, exist_ok=True)
    outcomes_path.write_text(
        json.dumps({"cycle": 1, "shadow_metrics": {}, "canonical_metrics": {}}) + "\n",
        encoding="utf-8",
    )
    evogate_path = tmp_path / "out" / "evogate_run.json"
    _write_json(
        evogate_path,
        {
            "run_id": "run",
            "ts": "2025-01-01T00:00:00Z",
            "pack_id": "pack",
            "applied_proposal_ids": [],
            "candidate_policy_path": "out/policies/candidate.json",
            "baseline_metrics_path": None,
            "replay": {"ok": True, "metric_deltas": {}, "notes": [], "provenance": {}},
            "promote_recommended": False,
            "thresholds": {},
            "notes": [],
            "provenance": {},
        },
    )
    ledger = UpgradeSpineLedger(tmp_path)
    candidates_sorted = sort_candidates(collect_candidates(tmp_path))
    for candidate in candidates_sorted:
        ledger.append("candidate", candidate.to_dict())
    entries = [e for e in ledger.read_entries() if e["entry_type"] == "candidate"]
    ids = [e["payload"]["candidate_id"] for e in entries]
    assert ids == [c.candidate_id for c in candidates_sorted]


def test_promote_uses_stored_patch_not_regenerated(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    candidate = _make_candidate()
    artifact, bundle = apply_candidate(candidate, tmp_path)
    gate_report = run_gates(
        bundle,
        candidate,
        artifact.sandbox_root,
        tmp_path,
        gate_overrides={
            "schema_validation": {"ok": True, "message": None},
            "dozen_run_invariance": {"ok": True, "verdict": "PASS"},
            "rent_enforcement": {"ok": True},
            "missing_input": {"ok": True},
        },
    )
    decision_payload = {
        "candidate_id": candidate.candidate_id,
        "status": "promote",
        "reasons": [],
        "gate_report": gate_report.to_dict(),
    }
    decision = UpgradeDecision(
        version="upgrade_decision.v0",
        run_id="test",
        created_at=utc_now_iso(),
        input_hash=compute_candidate_id(decision_payload),
        candidate_id=candidate.candidate_id,
        decision_id=compute_candidate_id(decision_payload),
        status="promote",
        reasons=[],
        gate_report=gate_report.to_dict(),
        not_computable=None,
    )
    artifact_dir = Path(bundle.artifact_dir)
    gate_path = artifact_dir / "gate_report.json"
    decision_path = artifact_dir / "decision.json"
    provenance_path = artifact_dir / "provenance.json"
    gate_path.write_text(
        json.dumps(gate_report.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    decision_path.write_text(
        json.dumps(decision.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    bundle_dict = bundle.to_dict()
    bundle_dict["gate_report"] = gate_report.to_dict()
    bundle_dict["decision_id"] = decision.decision_id
    provenance_path.write_text(
        json.dumps(bundle_dict, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    bundle_dict = finalize_artifact_bundle(artifact_dir, bundle_dict)
    patch_path = artifact_dir / "patch.diff"
    stored_patch = patch_path.read_text(encoding="utf-8")
    tmp_path.joinpath("SENTINEL.txt").write_text("do-not-affect\n", encoding="utf-8")
    ledger = UpgradeSpineLedger(tmp_path)
    ledger.append("decision", decision.to_dict())
    ledger.append("provenance_bundle", bundle_dict)
    receipt = promote_from_bundle(decision, artifact_dir, tmp_path)
    assert receipt
    assert patch_path.read_text(encoding="utf-8") == stored_patch
    assert "upgrade" in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_promote_refuses_if_not_promotable(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    candidate = _make_candidate()
    artifact, bundle = apply_candidate(candidate, tmp_path)
    artifact_dir = Path(bundle.artifact_dir)
    gate_report = {
        "order": [],
        "schema_validation": {"ok": True},
        "dozen_run_invariance": {"ok": False},
        "rent_enforcement": {"ok": True},
        "missing_input": {"ok": True},
        "overall_ok": False,
    }
    decision = UpgradeDecision(
        version="upgrade_decision.v0",
        run_id="test",
        created_at=utc_now_iso(),
        input_hash="hash",
        candidate_id=candidate.candidate_id,
        decision_id="decision",
        status="archive",
        reasons=["gates_failed"],
        gate_report=gate_report,
        not_computable=None,
    )
    artifact_dir.joinpath("gate_report.json").write_text(
        json.dumps(gate_report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    artifact_dir.joinpath("decision.json").write_text(
        json.dumps(decision.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    bundle_dict = bundle.to_dict()
    bundle_dict["gate_report"] = gate_report
    bundle_dict["decision_id"] = decision.decision_id
    artifact_dir.joinpath("provenance.json").write_text(
        json.dumps(bundle_dict, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    bundle_dict = finalize_artifact_bundle(artifact_dir, bundle_dict)
    with pytest.raises(ValueError):
        promote_from_bundle(decision, artifact_dir, tmp_path)
