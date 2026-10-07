"""A claim carries how strong it is, how far it reaches, and when it stops being one.

Grades alone cannot express this: a `real` observation from a narrow sample still only supports a
scoped claim, and a claim does not stay true forever. Modelled on the three properties the
literature proposes for evaluation claims (formality, scope, validity window).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import pytest

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
    # The field is a VALIDATED ClaimStrength, not a loose dict: the schema enforces itself at the
    # boundary rather than relying on a caller to remember to construct the model.
    assert isinstance(packet.claim_strength, ClaimStrength)
    assert packet.claim_strength.is_expired(now=NOW + timedelta(days=10)) is False


def test_a_malformed_claim_strength_is_rejected_at_construction() -> None:
    """A packet may not carry an unvalidated claim strength.

    `SourcePacket.claim_strength` was typed `Optional[Dict[str, Any]]`, so this passed silently while
    `ClaimStrength` -- which rejects exactly these values -- sat unused in production and was constructed
    only inside a test. A field whose type cannot fail is not a check; the validation existed and never
    ran on real data.
    """
    from pydantic import ValidationError

    from abraxas.sources.packets import SourcePacket

    with pytest.raises(ValidationError):
        SourcePacket(
            source_id="s1",
            observed_at_utc="2026-01-01T00:00:00Z",
            window_start_utc=None,
            window_end_utc=None,
            payload={},
            claim_strength={"formality": "vibes", "scope": "x", "validity_days": 1, "grounding": "moon"},
        )


def test_claim_strength_does_not_affect_the_packet_hash() -> None:
    """Typing the field must NOT pull it into the content hash -- it is metadata (Risk 3).

    Pins the exclusion through the type change: two packets identical except for `claim_strength` must
    hash identically.
    """
    from abraxas.sources.packets import SourcePacket

    common = {
        "source_id": "s1",
        "observed_at_utc": "2026-01-01T00:00:00Z",
        "window_start_utc": None,
        "window_end_utc": None,
        "payload": {"a": 1},
    }
    without = SourcePacket(**common)
    with_strength = SourcePacket(
        **common,
        claim_strength={
            "formality": "automated",
            "scope": "this sample",
            "validity_days": 30,
            "grounding": "field",
            "declared_at_utc": "2026-01-01T00:00:00+00:00",
        },
    )
    assert without.packet_hash() == with_strength.packet_hash()
    assert "claim_strength" not in without.canonical_payload()


def test_a_packet_without_claim_strength_declares_none() -> None:
    """The default must be absence, not a permissive default -- the Phase 1 rule."""
    from abraxas.sources.packets import SourcePacket

    packet = SourcePacket(
        source_id="s1", observed_at_utc="2026-01-01T00:00:00Z",
        window_start_utc=None, window_end_utc=None, payload={},
    )
    assert packet.claim_strength is None


class TestClaimStrengthDoesNotChangePacketIdentity:
    """A claim's declared strength must not change the identity of the observation.

    Phase 3 added `claim_strength` to `SourcePacket`, whose `packet_hash()` is derived from
    `canonical_payload()`. An un-excluded new field would therefore have changed EVERY packet hash
    in the repository -- silently, because nothing pins one. `canonical_payload()` excludes it.

    That exclusion is currently the only thing holding the property, and no other test in the suite
    would notice its removal. So the property is asserted here, both directions.
    """

    BASE: Dict[str, Any] = dict(
        source_id="s1",
        observed_at_utc="2026-01-01T00:00:00Z",
        window_start_utc=None,
        window_end_utc=None,
        payload={"x": 1},
    )

    def test_declaring_claim_strength_does_not_change_the_packet_hash(self) -> None:
        from abraxas.sources.packets import SourcePacket

        without = SourcePacket(**self.BASE)
        with_strength = SourcePacket(
            **self.BASE,
            claim_strength={
                "formality": "assessed",
                "scope": "this sample",
                "validity_days": 30,
                "grounding": "field",
            },
        )
        assert without.packet_hash() == with_strength.packet_hash(), (
            "adding a claim_strength declaration changed the packet hash. Declared strength is "
            "metadata ABOUT the claim, not part of the observation's identity -- the same "
            "identity-vs-metadata rule this repo applied to the rune hash and the lexicon content "
            "fingerprint."
        )

    def test_claim_strength_is_excluded_from_canonical_payload(self) -> None:
        from abraxas.evidence.claim_strength import ClaimStrength
        from abraxas.sources.packets import SourcePacket

        # A COMPLETE declaration: the field is a validated `ClaimStrength`, so a partial dict is
        # rejected at construction (see test_a_malformed_claim_strength_is_rejected_at_construction).
        # This test's subject is the EXCLUSION, not how permissive the field is.
        declared = {
            "formality": "automated",
            "scope": "this sample",
            "validity_days": 30,
            "grounding": "field",
        }
        packet = SourcePacket(**self.BASE, claim_strength=declared)

        assert "claim_strength" not in packet.canonical_payload()
        # ...while remaining present on the model, so the declaration is not lost.
        assert isinstance(packet.claim_strength, ClaimStrength)
        assert packet.claim_strength.formality == "automated"
        assert packet.claim_strength.scope == "this sample"

    def test_the_exclusion_is_scoped_and_identity_still_tracks_content(self) -> None:
        """The counterfactual. A blanket exclusion would also satisfy the test above.

        If someone 'fixed' a hash regression by excluding everything, `packet_hash()` would stop
        tracking the payload entirely -- identity would become a constant. This fails then.
        """
        from abraxas.sources.packets import SourcePacket

        a = SourcePacket(**self.BASE)
        b = SourcePacket(**{**self.BASE, "payload": {"x": 2}})
        assert a.packet_hash() != b.packet_hash(), (
            "changing the packet payload did not change its hash -- the exclusion is too broad, "
            "and identity no longer tracks content"
        )

    def test_the_exclusion_is_scoped_and_a_grade_still_matters(self) -> None:
        """Second counterfactual: the DATA GRADE is identity-bearing, unlike claim strength.

        If the exclusion were written as a blanket 'drop metadata' rule, the grade would vanish
        from the hash too -- and the grade is exactly what the rest of this work made
        load-bearing.
        """
        from abraxas.evidence.data_grade import SIMULATED
        from abraxas.sources.packets import SourcePacket

        a = SourcePacket(**self.BASE)
        b = SourcePacket(**{**self.BASE, "data_grade": SIMULATED})
        assert a.packet_hash() != b.packet_hash(), (
            "the data grade no longer participates in the packet hash"
        )
