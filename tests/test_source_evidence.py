"""Tests for SourceEvidencePacket.v1 - core/oracle/evidence.py"""
from __future__ import annotations

import pytest
from core.models.governance import Authority
from core.oracle.evidence import (
    SourceEvidencePacket,
    build_evidence_packet,
    build_provenance_chain,
    VALID_EVIDENCE_TYPES,
    VALID_STATUSES,
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


def test_build_evidence_packet_returns_valid(locked_authority):
    pkt = build_evidence_packet(
        evidence_id="ev-001",
        intake_hash="a" * 64,
        source_hash="b" * 64,
        evidence_type="structural",
        authority=locked_authority,
    )
    assert pkt.schema_version == "SourceEvidencePacket.v1"
    assert pkt.evidence_id == "ev-001"
    assert pkt.evidence_type == "structural"
    assert pkt.status == "valid"
    assert len(pkt.provenance_chain) == 3


def test_evidence_packet_provenance_chain_deterministic(locked_authority):
    pkt1 = build_evidence_packet("ev1", "a" * 64, "b" * 64, "structural", locked_authority)
    pkt2 = build_evidence_packet("ev1", "a" * 64, "b" * 64, "structural", locked_authority)
    assert pkt1.provenance_chain == pkt2.provenance_chain


def test_evidence_packet_missing_intake_hash_fail_closed(locked_authority):
    pkt = build_evidence_packet(
        evidence_id="ev-bad",
        intake_hash="",
        source_hash="b" * 64,
        evidence_type="structural",
        authority=locked_authority,
    )
    assert pkt.status == "not_computable"
    assert pkt.provenance_chain == []


def test_evidence_packet_missing_source_hash_fail_closed(locked_authority):
    pkt = build_evidence_packet(
        evidence_id="ev-bad",
        intake_hash="a" * 64,
        source_hash="",
        evidence_type="structural",
        authority=locked_authority,
    )
    assert pkt.status == "not_computable"
    assert pkt.provenance_chain == []


def test_evidence_packet_requires_locked_authority(unlocked_authority):
    with pytest.raises(ValueError, match="authority must be locked"):
        build_evidence_packet("ev1", "a" * 64, "b" * 64, "structural", unlocked_authority)


def test_evidence_packet_rejects_invalid_type(locked_authority):
    with pytest.raises(ValueError, match="evidence_type"):
        SourceEvidencePacket(
            evidence_id="ev1",
            intake_hash="a" * 64,
            source_hash="b" * 64,
            provenance_chain=["a", "b"],
            evidence_type="unknown",
            authority=locked_authority,
            status="valid",
        )


def test_evidence_packet_rejects_invalid_status(locked_authority):
    with pytest.raises(ValueError, match="status"):
        SourceEvidencePacket(
            evidence_id="ev1",
            intake_hash="a" * 64,
            source_hash="b" * 64,
            provenance_chain=["a", "b"],
            evidence_type="structural",
            authority=locked_authority,
            status="unknown_status",
        )


def test_all_evidence_types_accepted(locked_authority):
    for et in VALID_EVIDENCE_TYPES:
        pkt = build_evidence_packet("ev1", "a" * 64, "b" * 64, et, locked_authority)
        assert pkt.evidence_type == et


def test_evidence_hash_deterministic(locked_authority):
    pkt = build_evidence_packet("ev1", "a" * 64, "b" * 64, "structural", locked_authority)
    h1 = pkt.evidence_hash()
    h2 = pkt.evidence_hash()
    assert h1 == h2
    assert len(h1) == 64


def test_build_provenance_chain_deterministic():
    chain1 = build_provenance_chain("a" * 64, "b" * 64)
    chain2 = build_provenance_chain("a" * 64, "b" * 64)
    assert chain1 == chain2
    assert len(chain1) == 3


def test_build_provenance_chain_empty_for_missing_hashes():
    chain = build_provenance_chain("", "b" * 64)
    assert chain == []


def test_provenance_chain_differs_for_different_hashes():
    chain1 = build_provenance_chain("a" * 64, "b" * 64)
    chain2 = build_provenance_chain("c" * 64, "d" * 64)
    assert chain1 != chain2
