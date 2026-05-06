"""Tests for IntakeNormalizationPacket.v1 - core/oracle/normalization.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.normalization import (
    IntakeNormalizationPacket,
    build_normalization_packet,
    normalize_payload,
    hash_normalized,
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


def test_build_normalization_packet_returns_valid(locked_authority):
    pkt = build_normalization_packet(
        normalization_id="norm-001",
        source_hash="a" * 64,
        raw_payload={"key": "VALUE"},
        authority=locked_authority,
    )
    assert pkt.schema_version == "IntakeNormalizationPacket.v1"
    assert pkt.normalization_id == "norm-001"
    assert pkt.status == "complete"
    assert len(pkt.normalized_hash) == 64
    assert len(pkt.deterministic_normalization_hash) == 64


def test_normalization_hash_is_deterministic(locked_authority):
    pkt1 = build_normalization_packet("n1", "a" * 64, {"key": "VALUE"}, locked_authority)
    pkt2 = build_normalization_packet("n1", "a" * 64, {"key": "VALUE"}, locked_authority)
    assert pkt1.normalized_hash == pkt2.normalized_hash
    assert pkt1.deterministic_normalization_hash == pkt2.deterministic_normalization_hash


def test_identical_source_produces_identical_normalized_hash(locked_authority):
    """Identical source => identical normalized hash (determinism guarantee)."""
    payload = {"Z": "VALUE_Z", "A": "VALUE_A", "M": [3, 1, 2]}
    pkt1 = build_normalization_packet("n1", "a" * 64, payload, locked_authority)
    pkt2 = build_normalization_packet("n1", "a" * 64, payload, locked_authority)
    assert pkt1.normalized_hash == pkt2.normalized_hash


def test_different_payloads_produce_different_normalized_hash(locked_authority):
    pkt1 = build_normalization_packet("n1", "a" * 64, {"a": 1}, locked_authority)
    pkt2 = build_normalization_packet("n1", "a" * 64, {"a": 2}, locked_authority)
    assert pkt1.normalized_hash != pkt2.normalized_hash


def test_normalization_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        build_normalization_packet("n1", "a" * 64, {}, unlocked_authority)


def test_normalization_missing_source_hash_not_computable(locked_authority):
    pkt = build_normalization_packet("n1", "", {"key": "val"}, locked_authority)
    assert pkt.status == "not_computable"
    assert pkt.normalized_hash == ""
    assert pkt.deterministic_normalization_hash == ""


def test_normalize_payload_sorts_keys():
    payload = {"z": 1, "a": 2, "m": 3}
    result = normalize_payload(payload)
    # Result should be sorted dict
    assert list(result.keys()) == sorted(result.keys())


def test_normalize_payload_strips_none():
    payload = {"a": 1, "b": None, "c": "value"}
    result = normalize_payload(payload)
    assert "b" not in result
    assert "a" in result
    assert "c" in result


def test_normalize_payload_lowercases_strings():
    payload = {"key": "UPPER_CASE_VALUE"}
    result = normalize_payload(payload)
    assert result["key"] == "upper_case_value"


def test_normalize_payload_handles_nested_dicts():
    payload = {"outer": {"Z_key": "VALUE", "A_key": None}}
    result = normalize_payload(payload)
    # None values stripped, string values lowercased
    assert "A_key" not in result["outer"]  # None stripped
    assert result["outer"].get("Z_key") == "value"  # string lowercased


def test_normalize_payload_handles_lists():
    payload = {"items": ["B", "A", "C"]}
    result = normalize_payload(payload)
    # Lists are normalized (strings lowercased) but order preserved
    assert result["items"] == ["b", "a", "c"]


def test_normalization_steps_are_deterministic(locked_authority):
    pkt1 = build_normalization_packet("n1", "a" * 64, {"k": "v"}, locked_authority)
    pkt2 = build_normalization_packet("n1", "a" * 64, {"k": "v"}, locked_authority)
    assert pkt1.normalization_steps == pkt2.normalization_steps


def test_hash_normalized_deterministic():
    data = {"a": 1, "b": "value"}
    h1 = hash_normalized(data)
    h2 = hash_normalized(data)
    assert h1 == h2
    assert len(h1) == 64
