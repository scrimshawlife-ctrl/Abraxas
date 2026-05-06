"""Tests for receipt chaining."""
from __future__ import annotations
import pytest
from core.models.governance import Authority
from core.runes.receipts import RuneInvocationReceipt, build_receipt_chain

LOCKED_AUTHORITY = Authority(
    authority_id="auth.test.001",
    actor="test.actor",
    locked=True,
    scope="shadow_only",
)


def make_receipt(receipt_id, step_id="step-001", rune_id="RUNE_AUDIT", input_hash="abc", output_hash="def"):
    return RuneInvocationReceipt(
        receipt_id=receipt_id,
        execution_id="exec-001",
        rune_id=rune_id,
        pipeline_id="pipe-001",
        step_id=step_id,
        execution_state="completed",
        input_hash=input_hash,
        output_hash=output_hash,
        route_node="node.audit",
        authority=LOCKED_AUTHORITY,
        status="success",
        errors=[],
    )


def test_receipt_creation_succeeds():
    r = make_receipt("rcpt-001")
    assert r.schema_version == "RuneInvocationReceipt.v1"


def test_receipt_authority_locked():
    r = make_receipt("rcpt-001")
    assert r.authority.is_locked()


def test_receipt_hash_deterministic():
    r1 = make_receipt("rcpt-det")
    r2 = make_receipt("rcpt-det")
    assert r1.receipt_hash() == r2.receipt_hash()


def test_receipt_hash_changes_with_different_fields():
    r1 = make_receipt("rcpt-001", input_hash="hash-a")
    r2 = make_receipt("rcpt-001", input_hash="hash-b")
    assert r1.receipt_hash() != r2.receipt_hash()


def test_receipt_chain_builds():
    receipts = [make_receipt(f"rcpt-{i:03d}") for i in range(3)]
    chain = build_receipt_chain(receipts)
    assert "chain_hash" in chain
    assert chain["receipt_count"] == 3


def test_receipt_chain_hash_deterministic():
    r1 = [make_receipt(f"r-{i}") for i in range(2)]
    r2 = [make_receipt(f"r-{i}") for i in range(2)]
    c1 = build_receipt_chain(r1)
    c2 = build_receipt_chain(r2)
    assert c1["chain_hash"] == c2["chain_hash"]


def test_changing_receipt_breaks_chain():
    r1 = [make_receipt(f"r-{i}", input_hash="original") for i in range(3)]
    c1 = build_receipt_chain(r1)
    r2 = [make_receipt(f"r-{i}", input_hash="original") for i in range(3)]
    r2[1] = make_receipt("r-1", input_hash="TAMPERED")
    c2 = build_receipt_chain(r2)
    assert c1["chain_hash"] != c2["chain_hash"]


def test_empty_receipts_raises():
    with pytest.raises((ValueError, Exception)):
        build_receipt_chain([])


def test_receipt_invalid_execution_state():
    with pytest.raises((ValueError, Exception)):
        RuneInvocationReceipt(
            receipt_id="rcpt-bad",
            execution_id="exec-001",
            rune_id="RUNE_AUDIT",
            pipeline_id="pipe-001",
            step_id="step-001",
            execution_state="INVALID_STATE",
            input_hash="abc",
            output_hash="def",
            route_node="node.audit",
            authority=LOCKED_AUTHORITY,
            status="success",
            errors=[],
        )


def test_receipt_chain_orders_canonically():
    """Chain hash must be identical regardless of insertion order."""
    ra = make_receipt("zzz-receipt")
    rb = make_receipt("aaa-receipt")
    c1 = build_receipt_chain([ra, rb])
    c2 = build_receipt_chain([rb, ra])
    assert c1["chain_hash"] == c2["chain_hash"]
