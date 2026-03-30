from __future__ import annotations

from pathlib import Path


def test_readme_references_canonical_proof_and_promotion_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "python -m abx.cli proof-run --run-id <RUN_ID>" in readme
    assert "python -m abx.cli promotion-check --run-id <RUN_ID>" in readme
    assert "python -m abx.cli promotion-policy --run-id <RUN_ID>" in readme
    assert "make proof RUN_ID=<RUN_ID>" in readme
    assert "make promotion-check RUN_ID=<RUN_ID>" in readme
    assert "make promotion-policy RUN_ID=<RUN_ID>" in readme
    assert "python scripts/run_governance_lint.py" in readme
    assert "docs/RELEASE_READINESS.md" in readme


def test_validation_doc_keeps_tier_split_explicit() -> None:
    doc = Path("docs/VALIDATION_AND_ATTESTATION.md").read_text(encoding="utf-8")

    assert "Tier 1 — Local canonical closure" in doc
    assert "Tier 2 — Local promotion readiness bridge" in doc
    assert "Tier 2.5 — Federated readiness bridge" in doc
    assert "Tier 3 — Promotion-grade attestation execution" in doc
    assert "RemoteEvidenceManifest.v1" in doc


def test_docs_reference_shared_operator_projection_contract() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    runtime = Path("docs/CANONICAL_RUNTIME.md").read_text(encoding="utf-8")

    assert "OperatorProjectionSummary.v1" in readme
    assert "abx/operator_projection.py" in runtime
    assert "/runs/{run_id}/projection.json" in runtime
    assert "/api/operator/projection/:runId" in runtime


def test_docs_mark_legacy_acceptance_and_seal_as_shadow_paths() -> None:
    validation_doc = Path("docs/VALIDATION_AND_ATTESTATION.md").read_text(encoding="utf-8")
    inventory_doc = Path("docs/SUBSYSTEM_INVENTORY.md").read_text(encoding="utf-8")

    assert "abx.cli acceptance" in validation_doc
    assert "scripts/seal_release.py" in validation_doc
    assert "CANONICAL_GATED" in inventory_doc
    assert "SHADOW_DIAGNOSTIC" in inventory_doc
    assert "STABILIZE_SHADOW" in inventory_doc
    assert "DEPRECATE_OR_RETIRE" in inventory_doc
