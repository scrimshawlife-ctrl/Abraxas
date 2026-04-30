from __future__ import annotations

from pathlib import Path

from abraxas.governance.attestation_runner import run_attestation
from abraxas.governance.binding_validator import validate_bindings
from abraxas.governance.repair_suggester import suggest_repairs
from scripts.run_patch004_meta_governance import build_bundle


def test_attestation_is_deterministic_and_sorted() -> None:
    first = run_attestation(repo_root=".", timestamp="1970-01-01T00:00:00Z")
    second = run_attestation(repo_root=".", timestamp="1970-01-01T00:00:00Z")
    assert first == second
    assert first["files_indexed"] == sorted(first["files_indexed"])


def test_missing_subsystems_are_flagged() -> None:
    report = validate_bindings(repo_root=".")
    states = {item["id"]: item["status"] for item in report["subsystems"]}
    assert states["cross_domain_fusion"] in {"PRESENT", "PARTIAL"}
    assert states["pse_outcome_tracker"] in {"PRESENT", "PARTIAL"}
    assert states["brier_ledger"] in {"PRESENT", "PARTIAL"}


def test_repair_suggestions_deterministic() -> None:
    validation = validate_bindings(repo_root=".")
    first = suggest_repairs(validation)
    second = suggest_repairs(validation)
    assert first == second


def test_output_bundle_contains_sections() -> None:
    bundle = build_bundle(Path("."), "1970-01-01T00:00:00Z")
    assert bundle["schema_version"] == "Patch004MetaGovernanceBundle.v1"
    assert "attestation" in bundle
    assert "binding_validation" in bundle
    assert "repair_suggestions" in bundle


def test_pse_path_present() -> None:
    assert Path("abraxas/pse/brier_ledger.py").exists()
