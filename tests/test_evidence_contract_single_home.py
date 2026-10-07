"""Tests verifying the EvidenceEnvelope contract has a single canonical home.

Plan: single-home-the-evidence-contract, Phase 1.
"""

from dataclasses import fields

from abraxas.evidence import EvidenceEnvelope
from abraxas.evidence.contract import EvidenceEnvelope as ContractEnvelope


def test_evidence_envelope_single_home_identity():
    """The package-level EvidenceEnvelope IS the contract copy — not a duplicate."""
    assert EvidenceEnvelope is ContractEnvelope, (
        "EvidenceEnvelope must be a single canonical type. "
        "The package __init__ must re‑export the contract copy, not redefine it."
    )


def test_evidence_envelope_field_count():
    """The canonical envelope has exactly 21 fields (no schema_version divergence)."""
    field_names = [f.name for f in fields(EvidenceEnvelope)]
    assert len(field_names) == 21, (
        f"Expected 21 fields (no schema_version), got {len(field_names)}: {field_names}"
    )
    assert "schema_version" not in field_names, (
        "schema_version was deliberately removed — it was read by zero external consumers."
    )