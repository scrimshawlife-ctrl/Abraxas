"""A claim carries how strong it is, how far it reaches, and when it stops being one.

Grades alone cannot express this: a `real` observation from a narrow sample still only supports a
scoped claim, and a claim does not stay true forever. Modelled on the three properties the
literature proposes for evaluation claims (formality, scope, validity window).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from abraxas.evidence.claim_strength import (
    FORMALITY_TIERS,
    ClaimStrength,
    groundings_for,
)


NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_declared_in_full_round_trips() -> None:
    cs = ClaimStrength(
        formality="assessed",
        scope="this sample only",
        validity_days=30,
        grounding="field",
    )
    assert cs.formality == "assessed"
    assert cs.grounding == "field"


def test_formality_must_be_a_known_tier() -> None:
    try:
        ClaimStrength(formality="vibes", scope="x", validity_days=1, grounding="field")
    except ValueError as exc:
        assert "formality" in str(exc)
    else:
        raise AssertionError("an unknown formality tier was accepted")


def test_grounding_must_be_a_known_level() -> None:
    try:
        ClaimStrength(formality="assessed", scope="x", validity_days=1, grounding="moon")
    except ValueError as exc:
        assert "grounding" in str(exc)
    else:
        raise AssertionError("an unknown grounding level was accepted")


def test_scope_must_not_be_blank() -> None:
    try:
        ClaimStrength(formality="assessed", scope="   ", validity_days=1, grounding="field")
    except ValueError as exc:
        assert "scope" in str(exc)
    else:
        raise AssertionError("a blank scope was accepted")


def test_a_claim_expires_after_its_validity_window() -> None:
    cs = ClaimStrength(
        formality="assessed", scope="x", validity_days=14, grounding="field",
        declared_at_utc="2026-01-01T00:00:00+00:00",
    )
    assert cs.is_expired(now=NOW + timedelta(days=13)) is False
    assert cs.is_expired(now=NOW + timedelta(days=15)) is True


def test_expiry_is_evaluated_against_an_INJECTED_clock() -> None:
    """The clock must be injectable, or the test is a time bomb."""
    cs = ClaimStrength(
        formality="assessed", scope="x", validity_days=1, grounding="field",
        declared_at_utc="2099-01-01T00:00:00+00:00",
    )
    assert cs.is_expired(now=NOW) is False


def test_an_undeclared_timestamp_expires_immediately() -> None:
    """Absence is not a licence to treat a claim as fresh -- the Phase 1 rule, again."""
    cs = ClaimStrength(formality="assessed", scope="x", validity_days=365, grounding="field")
    assert cs.is_expired(now=NOW) is True


def test_every_grade_maps_to_a_grounding_level() -> None:
    from abraxas.evidence.data_grade import DERIVED, REAL, SIMULATED, UNDECLARED

    assert groundings_for(REAL) == "field"
    assert groundings_for(SIMULATED) == "lab"
    assert groundings_for(DERIVED) == "derived"
    assert groundings_for(UNDECLARED) is None


def test_formality_tiers_are_ordered_strongest_first() -> None:
    assert FORMALITY_TIERS[0] == "assessed"
    assert FORMALITY_TIERS[-1] == "automated"


def test_a_packet_may_declare_claim_strength() -> None:
    from abraxas.sources.packets import SourcePacket

    packet = SourcePacket(
        source_id="s1",
        observed_at_utc="2026-01-01T00:00:00Z",
        window_start_utc=None,
        window_end_utc=None,
        payload={},
        claim_strength={
            "formality": "automated",
            "scope": "this sample",
            "validity_days": 30,
            "grounding": "field",
            "declared_at_utc": "2026-01-01T00:00:00+00:00",
        },
    )
    strength = ClaimStrength(**packet.claim_strength)
    assert strength.is_expired(now=NOW + timedelta(days=10)) is False


def test_a_packet_without_claim_strength_declares_none() -> None:
    """The default must be absence, not a permissive default -- the Phase 1 rule."""
    from abraxas.sources.packets import SourcePacket

    packet = SourcePacket(
        source_id="s1", observed_at_utc="2026-01-01T00:00:00Z",
        window_start_utc=None, window_end_utc=None, payload={},
    )
    assert packet.claim_strength is None
