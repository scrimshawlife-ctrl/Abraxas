from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.run_patch004_meta_governance import build_bundle
from scripts.run_pse_e2e_fixture_validation import run_validation

FORBIDDEN_TERMS = ("learning", "adaptive", "weight", "portfolio", "strategy", "api")
OPTIONAL_HASH_ARTIFACTS = [
    "out/reports/pse_outcome_ledger.latest.json",
    "out/reports/pse_brier_ledger.latest.json",
]
REQUIRED_HASH_ARTIFACTS = [
    "out/reports/patch004_meta_governance.latest.json",
    "out/reports/pse_e2e_fixture_validation.latest.json",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PATCH009_FILES = [
    "scripts/run_abx_readiness_gate.py",
    "tests/test_abx_readiness_gate.py",
]

def _forbidden_violations(repo_root: Path) -> list[str]:
    violations: list[str] = []
    for rel in PATCH009_FILES:
        file_path = repo_root / rel
        if not file_path.exists():
            continue
        text = file_path.read_text(encoding="utf-8", errors="ignore").lower()
        if any(term in text for term in FORBIDDEN_TERMS):
            violations.append(rel)
    return sorted(set(violations))


def _run_once(repo_root: Path) -> tuple[dict, dict, dict]:
    bundle = build_bundle(repo_root, "1970-01-01T00:00:00Z")
    validation = run_validation()

    reports_dir = repo_root / "out" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "patch004_meta_governance.latest.json").write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (reports_dir / "pse_e2e_fixture_validation.latest.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    hashes = {}
    for rel in REQUIRED_HASH_ARTIFACTS + OPTIONAL_HASH_ARTIFACTS:
        p = repo_root / rel
        if p.exists():
            hashes[rel] = _sha256(p)
    return bundle, validation, hashes


def run_readiness_gate(repo_root: str | Path) -> dict:
    root = Path(repo_root).resolve()
    bundle_1, e2e_1, hashes_1 = _run_once(root)
    bundle_2, e2e_2, hashes_2 = _run_once(root)

    checks = [
        {"id": "validator_clean", "status": "PASS" if bundle_2["binding_validation"].get("missing_subsystems") == [] else "FAIL"},
        {"id": "e2e_pass", "status": "PASS" if e2e_2.get("status") == "PASS" else "FAIL"},
        {"id": "hash_invariance", "status": "PASS" if hashes_1 == hashes_2 else "FAIL"},
        {"id": "mean_brier_expected", "status": "PASS" if e2e_2.get("brier_summary", {}).get("mean_brier") == 0.1975 else "FAIL"},
        {"id": "scored_count_expected", "status": "PASS" if e2e_2.get("brier_summary", {}).get("scored_count") == 3 else "FAIL"},
        {"id": "forbidden_artifacts", "status": "PASS" if not _forbidden_violations(root) else "FAIL"},
    ]
    ready = all(item["status"] == "PASS" for item in checks)

    return {
        "schema_version": "ABXReadinessGateReport.v1",
        "status": "READY" if ready else "NOT_READY",
        "authority": "READINESS_GATE",
        "checks": checks,
        "artifact_hashes": {"run_1": hashes_1, "run_2": hashes_2},
    }
