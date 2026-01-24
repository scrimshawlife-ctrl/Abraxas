from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from server.abraxas.upgrade_spine.ledger import UpgradeSpineLedger
from server.abraxas.upgrade_spine.types import UpgradeCandidate
from server.abraxas.upgrade_spine.utils import compute_candidate_id, utc_now_iso
from tools.genesis_proof_upgrade_spine import run_genesis_proof


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Genesis Tests"],
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


def _make_docs_candidate() -> UpgradeCandidate:
    patch_plan = {
        "format_version": "0.1",
        "operations": [
            {"op": "write_file", "path": "README.md", "content": "baseline\ngenesis\n"},
        ],
        "notes": ["genesis_docs_only"],
    }
    payload = {
        "source_loop": "manual",
        "change_type": "docs_only",
        "target_paths": ["README.md"],
        "patch_plan": patch_plan,
        "evidence_refs": [],
        "constraints": {"safe_canary": True},
        "not_computable": None,
    }
    candidate_id = compute_candidate_id(payload)
    return UpgradeCandidate(
        version="upgrade_candidate.v0",
        run_id="genesis",
        created_at=utc_now_iso(),
        input_hash=compute_candidate_id(payload),
        candidate_id=candidate_id,
        source_loop="manual",
        change_type="docs_only",
        target_paths=["README.md"],
        patch_plan=patch_plan,
        evidence_refs=[],
        constraints={"safe_canary": True},
        not_computable=None,
    )


def test_golden_state_marker_exists() -> None:
    marker = Path(".aal/cap/GOLDEN_STATE.json")
    assert marker.exists()
    payload = json.loads(marker.read_text(encoding="utf-8"))
    for key in [
        "cap_version",
        "created_at",
        "git_commit",
        "repo_fingerprint",
        "upgrade_spine_version",
        "notes",
    ]:
        assert key in payload


def test_genesis_proof_refuses_without_safe_candidate(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    receipt = run_genesis_proof(
        tmp_path,
        gate_overrides={
            "schema_validation": {"ok": True, "message": None},
            "dozen_run_invariance": {"ok": True, "verdict": "PASS"},
            "rent_enforcement": {"ok": True},
            "missing_input": {"ok": True},
        },
    )
    assert receipt["status"] == "NOT_COMPUTABLE"


def test_genesis_proof_promotes_from_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _init_git_repo(tmp_path)
    ledger = UpgradeSpineLedger(tmp_path)
    candidate = _make_docs_candidate()
    ledger.append("candidate", candidate.to_dict())
    used = {"called": False}

    def _sentinel(*args, **kwargs):
        used["called"] = True
        from server.abraxas.upgrade_spine.upgrade_manager import promote_from_bundle

        return promote_from_bundle(*args, **kwargs)

    monkeypatch.setattr("tools.genesis_proof_upgrade_spine.promote_from_bundle", _sentinel)
    receipt = run_genesis_proof(
        tmp_path,
        gate_overrides={
            "schema_validation": {"ok": True, "message": None},
            "dozen_run_invariance": {"ok": True, "verdict": "PASS"},
            "rent_enforcement": {"ok": True},
            "missing_input": {"ok": True},
        },
    )
    assert used["called"] is True
    assert receipt["status"] == "OK"
