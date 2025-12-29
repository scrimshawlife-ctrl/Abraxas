"""Tests for Promotion Ledger Hash Chain

Ensures hash chain integrity and tamper detection.
"""

import json
import tempfile
from pathlib import Path

import pytest

from abraxas.metrics.governance import (
    EvidenceBundle,
    LiftMetrics,
    PromotionDecision,
    PromotionLedgerEntry,
    RedundancyScores,
    StabilizationScores,
    TestResults,
)
from abraxas.metrics.hashutil import hash_json, verify_hash_chain
from abraxas.metrics.registry_io import PromotionLedger


@pytest.fixture
def evidence_bundle():
    """Create sample evidence bundle."""
    return EvidenceBundle(
        metric_id="TEST_METRIC",
        timestamp="2025-12-26T00:00:00Z",
        sim_version="1.0.0",
        seeds_used=[42, 43, 44],
        outcome_ledger_slice_hashes=["a" * 64, "b" * 64],
        test_results=TestResults(
            provenance_passed=True,
            falsifiability_passed=True,
            redundancy_passed=True,
            rent_payment_passed=True,
            ablation_passed=True,
            stabilization_passed=True,
        ),
        lift_metrics=LiftMetrics(
            forecast_error_delta=-0.03,
            brier_delta=-0.01,
            calibration_delta=0.06,
            misinfo_auc_delta=0.04,
            world_media_divergence_explained_delta=0.07,
        ),
        redundancy_scores=RedundancyScores(
            max_corr=0.45,
            mutual_info=0.12,
            nearest_metric_ids=["METRIC_A", "METRIC_B"],
        ),
        stabilization_scores=StabilizationScores(
            cycles_required=5,
            cycles_passed=6,
            drift_tests_passed=2,
            performance_variance=0.02,
        ),
        ablation_results={"forecast_error_degradation": 0.03},
    )


def test_hash_json_deterministic():
    """Test that hash_json is deterministic."""
    obj = {"key": "value", "number": 3.14159, "list": [1, 2, 3]}

    hash1 = hash_json(obj)
    hash2 = hash_json(obj)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length


def test_hash_json_key_order_independent():
    """Test that key order doesn't affect hash."""
    obj1 = {"a": 1, "b": 2, "c": 3}
    obj2 = {"c": 3, "a": 1, "b": 2}

    hash1 = hash_json(obj1)
    hash2 = hash_json(obj2)

    assert hash1 == hash2


def test_hash_json_different_objects():
    """Test that different objects produce different hashes."""
    obj1 = {"key": "value1"}
    obj2 = {"key": "value2"}

    hash1 = hash_json(obj1)
    hash2 = hash_json(obj2)

    assert hash1 != hash2


def test_promotion_entry_signature(evidence_bundle):
    """Test promotion entry signature creation."""
    entry = PromotionLedgerEntry.create_entry(
        metric_id="TEST_METRIC",
        candidate_version="0.1.0",
        sim_version="1.0.0",
        evidence_bundle=evidence_bundle,
        decision=PromotionDecision.PROMOTED,
        rationale="All gates passed",
        prev_hash="0" * 64,
    )

    # Signature should be non-empty and hex
    assert len(entry.signature) == 64
    assert all(c in "0123456789abcdef" for c in entry.signature)

    # Evidence bundle hash should match
    assert entry.evidence_bundle_hash == evidence_bundle.compute_hash()


def test_hash_chain_single_entry(evidence_bundle):
    """Test hash chain with single entry."""
    entry = PromotionLedgerEntry.create_entry(
        metric_id="TEST_METRIC",
        candidate_version="0.1.0",
        sim_version="1.0.0",
        evidence_bundle=evidence_bundle,
        decision=PromotionDecision.PROMOTED,
        rationale="Test",
        prev_hash="0" * 64,
    )

    entries = [entry.to_dict()]
    assert verify_hash_chain(entries, prev_hash_key="prev_hash") is True


def test_hash_chain_multiple_entries(evidence_bundle):
    """Test hash chain with multiple entries."""
    # Entry 1 (genesis)
    entry1 = PromotionLedgerEntry.create_entry(
        metric_id="METRIC_1",
        candidate_version="0.1.0",
        sim_version="1.0.0",
        evidence_bundle=evidence_bundle,
        decision=PromotionDecision.PROMOTED,
        rationale="First",
        prev_hash="0" * 64,
    )

    # Compute hash of entry1 (excluding signature)
    entry1_dict = {k: v for k, v in entry1.to_dict().items() if k != "signature"}
    hash1 = hash_json(entry1_dict)

    # Entry 2 (chained)
    entry2 = PromotionLedgerEntry.create_entry(
        metric_id="METRIC_2",
        candidate_version="0.1.0",
        sim_version="1.0.0",
        evidence_bundle=evidence_bundle,
        decision=PromotionDecision.PROMOTED,
        rationale="Second",
        prev_hash=hash1,
    )

    # Verify chain
    entries = [entry1.to_dict(), entry2.to_dict()]
    assert verify_hash_chain(entries, prev_hash_key="prev_hash") is True


def test_hash_chain_tamper_detection(evidence_bundle):
    """Test that tampered chain is detected."""
    # Create valid chain
    entry1 = PromotionLedgerEntry.create_entry(
        metric_id="METRIC_1",
        candidate_version="0.1.0",
        sim_version="1.0.0",
        evidence_bundle=evidence_bundle,
        decision=PromotionDecision.PROMOTED,
        rationale="First",
        prev_hash="0" * 64,
    )

    entry1_dict = {k: v for k, v in entry1.to_dict().items() if k != "signature"}
    hash1 = hash_json(entry1_dict)

    entry2 = PromotionLedgerEntry.create_entry(
        metric_id="METRIC_2",
        candidate_version="0.1.0",
        sim_version="1.0.0",
        evidence_bundle=evidence_bundle,
        decision=PromotionDecision.PROMOTED,
        rationale="Second",
        prev_hash=hash1,
    )

    entries = [entry1.to_dict(), entry2.to_dict()]

    # Verify original chain is valid
    assert verify_hash_chain(entries, prev_hash_key="prev_hash") is True

    # Tamper with entry2's prev_hash
    entries[1]["prev_hash"] = "f" * 64

    # Verify tampered chain is invalid
    assert verify_hash_chain(entries, prev_hash_key="prev_hash") is False


def test_promotion_ledger_append_and_verify(evidence_bundle):
    """Test promotion ledger append and verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "promotions.jsonl"
        chain_path = Path(tmpdir) / "promotions_chain.jsonl"

        ledger = PromotionLedger(ledger_path=ledger_path, chain_path=chain_path)

        # Append first entry
        entry1 = PromotionLedgerEntry.create_entry(
            metric_id="METRIC_1",
            candidate_version="0.1.0",
            sim_version="1.0.0",
            evidence_bundle=evidence_bundle,
            decision=PromotionDecision.PROMOTED,
            rationale="First promotion",
            prev_hash="0" * 64,
        )
        ledger.append(entry1)

        # Append second entry (chained)
        prev_hash = ledger.get_last_hash()
        entry2 = PromotionLedgerEntry.create_entry(
            metric_id="METRIC_2",
            candidate_version="0.1.0",
            sim_version="1.0.0",
            evidence_bundle=evidence_bundle,
            decision=PromotionDecision.PROMOTED,
            rationale="Second promotion",
            prev_hash=prev_hash,
        )
        ledger.append(entry2)

        # Verify chain integrity
        assert ledger.verify_chain() is True
        assert len(ledger.entries) == 2


def test_promotion_ledger_load_from_disk(evidence_bundle):
    """Test loading ledger from disk preserves chain."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "promotions.jsonl"
        chain_path = Path(tmpdir) / "promotions_chain.jsonl"

        # Create and save ledger
        ledger1 = PromotionLedger(ledger_path=ledger_path, chain_path=chain_path)

        entry = PromotionLedgerEntry.create_entry(
            metric_id="METRIC_1",
            candidate_version="0.1.0",
            sim_version="1.0.0",
            evidence_bundle=evidence_bundle,
            decision=PromotionDecision.PROMOTED,
            rationale="Test",
            prev_hash="0" * 64,
        )
        ledger1.append(entry)

        # Load from disk
        ledger2 = PromotionLedger(ledger_path=ledger_path, chain_path=chain_path)

        # Verify loaded ledger has same entry
        assert len(ledger2.entries) == 1
        assert ledger2.entries[0].metric_id == "METRIC_1"
        assert ledger2.verify_chain() is True


def test_evidence_bundle_hash_deterministic(evidence_bundle):
    """Test evidence bundle hash is deterministic."""
    hash1 = evidence_bundle.compute_hash()
    hash2 = evidence_bundle.compute_hash()

    assert hash1 == hash2
    assert len(hash1) == 64
