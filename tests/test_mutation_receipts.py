"""Tests for MutationProposalReceipt.v1 - core/sandbox/receipts.py"""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.sandbox.receipts import (
    MutationProposalReceipt,
    build_mutation_receipt,
)


@pytest.fixture
def auth() -> Authority:
    return Authority(
        authority_id="auth.receipt.001",
        actor="system.receipt",
        locked=True,
        scope="sandbox_only",
    )


def test_build_mutation_receipt_returns_valid_receipt(auth):
    receipt = build_mutation_receipt(
        receipt_id="r-001",
        mutation_hash="a" * 64,
        branch_hash="b" * 64,
        replay_hash="c" * 64,
        stabilization_hash="d" * 64,
        authority=auth,
    )
    assert receipt.schema_version == "MutationProposalReceipt.v1"
    assert receipt.status == "issued"
    assert receipt.receipt_id == "r-001"


def test_receipt_hash_is_deterministic(auth):
    r1 = build_mutation_receipt("r", "a" * 64, "b" * 64, "c" * 64, "d" * 64, auth)
    r2 = build_mutation_receipt("r", "a" * 64, "b" * 64, "c" * 64, "d" * 64, auth)
    assert r1.receipt_hash() == r2.receipt_hash()


def test_receipt_hash_differs_for_different_inputs(auth):
    r1 = build_mutation_receipt("r1", "a" * 64, "b" * 64, "c" * 64, "d" * 64, auth)
    r2 = build_mutation_receipt("r2", "e" * 64, "f" * 64, "g" * 64, "h" * 64, auth)
    assert r1.receipt_hash() != r2.receipt_hash()


def test_authority_must_be_locked():
    bad_auth = Authority(
        authority_id="bad", actor="x", locked=False, scope="sandbox_only"
    )
    with pytest.raises(ValueError, match="authority must be locked"):
        MutationProposalReceipt(
            receipt_id="r",
            mutation_hash="a" * 64,
            branch_hash="b" * 64,
            replay_hash="c" * 64,
            stabilization_hash="d" * 64,
            authority=bad_auth,
            status="issued",
        )


def test_invalid_status_raises(auth):
    with pytest.raises(ValueError, match="status"):
        MutationProposalReceipt(
            receipt_id="r",
            mutation_hash="a" * 64,
            branch_hash="b" * 64,
            replay_hash="c" * 64,
            stabilization_hash="d" * 64,
            authority=auth,
            status="bad_status",
        )


def test_receipt_hash_changes_with_status(auth):
    r1 = MutationProposalReceipt(
        receipt_id="r",
        mutation_hash="a" * 64,
        branch_hash="b" * 64,
        replay_hash="c" * 64,
        stabilization_hash="d" * 64,
        authority=auth,
        status="issued",
    )
    r2 = MutationProposalReceipt(
        receipt_id="r",
        mutation_hash="a" * 64,
        branch_hash="b" * 64,
        replay_hash="c" * 64,
        stabilization_hash="d" * 64,
        authority=auth,
        status="validated",
    )
    assert r1.receipt_hash() != r2.receipt_hash()


def test_all_valid_statuses(auth):
    for status in ("issued", "validated", "invalidated", "expired"):
        r = MutationProposalReceipt(
            receipt_id="r",
            mutation_hash="a" * 64,
            branch_hash="b" * 64,
            replay_hash="c" * 64,
            stabilization_hash="d" * 64,
            authority=auth,
            status=status,
        )
        assert r.status == status


def test_receipt_hash_includes_all_fields(auth):
    """Changing any field must change the hash."""
    base = {"receipt_id": "r", "mutation_hash": "a" * 64, "branch_hash": "b" * 64,
            "replay_hash": "c" * 64, "stabilization_hash": "d" * 64,
            "authority": auth, "status": "issued"}

    r_base = MutationProposalReceipt(**base)
    base_hash = r_base.receipt_hash()

    for field, new_val in [
        ("mutation_hash", "z" * 64),
        ("branch_hash", "y" * 64),
        ("replay_hash", "x" * 64),
        ("stabilization_hash", "w" * 64),
    ]:
        modified = dict(base)
        modified[field] = new_val
        r_mod = MutationProposalReceipt(**modified)
        assert r_mod.receipt_hash() != base_hash, f"Hash should differ when {field} changes"
