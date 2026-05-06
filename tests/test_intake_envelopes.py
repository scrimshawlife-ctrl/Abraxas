"""Tests for IntakeEnvelope.v1 - core/oracle/intake.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.intake import (
    IntakeEnvelope,
    build_intake_envelope,
    hash_payload,
    VALID_SOURCE_TYPES,
    VALID_INTAKE_STATUSES,
)


@pytest.fixture
def locked_authority() -> Authority:
    return Authority(
        authority_id="auth.test.001",
        actor="system.test",
        locked=True,
        scope="oracle_intake_only",
    )


@pytest.fixture
def unlocked_authority() -> Authority:
    return Authority(
        authority_id="auth.test.bad",
        actor="system.test",
        locked=False,
        scope="oracle_intake_only",
    )


def test_build_intake_envelope_returns_valid(locked_authority):
    env = build_intake_envelope(
        intake_id="intake-001",
        source_id="src-001",
        source_type="document",
        intake_timestamp_index=0,
        raw_payload={"key": "value"},
        authority=locked_authority,
    )
    assert env.schema_version == "IntakeEnvelope.v1"
    assert env.intake_id == "intake-001"
    assert env.source_id == "src-001"
    assert env.source_type == "document"
    assert env.intake_timestamp_index == 0
    assert env.intake_status == "pending"
    assert len(env.raw_payload_hash) == 64


def test_intake_envelope_hash_is_deterministic(locked_authority):
    env1 = build_intake_envelope("id1", "src1", "document", 0, {"a": 1}, locked_authority)
    env2 = build_intake_envelope("id1", "src1", "document", 0, {"a": 1}, locked_authority)
    assert env1.raw_payload_hash == env2.raw_payload_hash
    assert env1.envelope_hash() == env2.envelope_hash()


def test_intake_envelope_hash_differs_for_different_payloads(locked_authority):
    env1 = build_intake_envelope("id1", "src1", "document", 0, {"a": 1}, locked_authority)
    env2 = build_intake_envelope("id1", "src1", "document", 0, {"a": 2}, locked_authority)
    assert env1.raw_payload_hash != env2.raw_payload_hash


def test_intake_envelope_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        build_intake_envelope("id1", "src1", "document", 0, {}, unlocked_authority)


def test_intake_envelope_rejects_invalid_source_type(locked_authority):
    with pytest.raises(ValueError, match="source_type"):
        IntakeEnvelope(
            intake_id="id1",
            source_id="src1",
            source_type="unknown_type",
            intake_timestamp_index=0,
            raw_payload_hash="a" * 64,
            authority=locked_authority,
            intake_status="pending",
        )


def test_intake_envelope_rejects_invalid_status(locked_authority):
    with pytest.raises(ValueError, match="intake_status"):
        IntakeEnvelope(
            intake_id="id1",
            source_id="src1",
            source_type="document",
            intake_timestamp_index=0,
            raw_payload_hash="a" * 64,
            authority=locked_authority,
            intake_status="unknown_status",
        )


def test_intake_envelope_rejects_negative_timestamp_index(locked_authority):
    with pytest.raises(ValueError, match="intake_timestamp_index"):
        IntakeEnvelope(
            intake_id="id1",
            source_id="src1",
            source_type="document",
            intake_timestamp_index=-1,
            raw_payload_hash="a" * 64,
            authority=locked_authority,
            intake_status="pending",
        )


def test_intake_envelope_with_normalized_payload_hash(locked_authority):
    env = build_intake_envelope(
        intake_id="id1",
        source_id="src1",
        source_type="document",
        intake_timestamp_index=0,
        raw_payload={"key": "VALUE"},
        authority=locked_authority,
        normalized_payload={"key": "value"},
    )
    assert env.normalized_payload_hash is not None
    assert len(env.normalized_payload_hash) == 64
    assert env.normalized_payload_hash != env.raw_payload_hash


def test_all_source_types_are_valid(locked_authority):
    for stype in VALID_SOURCE_TYPES:
        env = build_intake_envelope("id1", "src1", stype, 0, {}, locked_authority)
        assert env.source_type == stype


def test_all_intake_statuses_are_valid(locked_authority):
    for status in VALID_INTAKE_STATUSES:
        env = IntakeEnvelope(
            intake_id="id1",
            source_id="src1",
            source_type="document",
            intake_timestamp_index=0,
            raw_payload_hash="a" * 64,
            authority=locked_authority,
            intake_status=status,
        )
        assert env.intake_status == status


def test_hash_payload_is_deterministic():
    payload = {"z": 3, "a": 1, "m": [1, 2, 3]}
    h1 = hash_payload(payload)
    h2 = hash_payload(payload)
    assert h1 == h2
    assert len(h1) == 64


def test_hash_payload_differs_for_different_inputs():
    h1 = hash_payload({"a": 1})
    h2 = hash_payload({"a": 2})
    assert h1 != h2


def test_intake_timestamp_index_monotonic_across_builds(locked_authority):
    env0 = build_intake_envelope("id0", "src0", "document", 0, {}, locked_authority)
    env1 = build_intake_envelope("id1", "src1", "document", 1, {}, locked_authority)
    env2 = build_intake_envelope("id2", "src2", "document", 2, {}, locked_authority)
    assert env0.intake_timestamp_index < env1.intake_timestamp_index < env2.intake_timestamp_index
