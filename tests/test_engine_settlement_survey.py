"""Guard the survey that guards the settlement records.

A settlement record is a claim. `tests/test_engine_manifest_agreement.py` enforces its SHAPE (values
from the closed set; `settled` must cite evidence). It cannot enforce that the claim is TRUE -- a
`settled` value with a plausible-looking evidence path satisfies it.

This module links the manifest to `scripts/survey_engine_settlements.py`, which evaluates each engine
against the doctrine's technical-settlement criteria and refuses to certify a settlement resting on an
unmeasured criterion. Together: the agreement guard enforces shape, the survey enforces corroboration.

Both files exist because of the pattern this repository keeps relearning: *a status document is a
claim, not evidence* -- and a field that nothing checks decays, which is what the arXiv scan measured
in the wild where evaluation sections have the lowest fill-out rates of any model-card section.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from survey_engine_settlements import (  # noqa: E402
    PRESENT,
    UNMEASURED,
    _collected_test_ids,
    survey,
    uncorroborated_settlements,
)


def _row(engine: str, declared: str, satisfiable: bool) -> dict:
    return {"engine": engine, "declared_technical": declared, "technical_satisfiable": satisfiable}


# --------------------------------------------------------------------------------------------
# The real state
# --------------------------------------------------------------------------------------------


def test_the_survey_agrees_with_the_manifest() -> None:
    """No engine may declare a technical settlement the survey cannot corroborate."""
    lying = uncorroborated_settlements(survey())
    assert lying == [], (
        f"engines declaring `settled` without every criterion present: {lying}. "
        "Either supply the evidence, or leave the settlement unsettled."
    )


def test_every_engine_in_the_manifest_is_surveyed() -> None:
    """A survey that silently omits an engine is not a survey."""
    from abraxas.engines.manifest import ENGINES

    surveyed = {r["engine"] for r in survey()}
    expected = {spec.name for spec in ENGINES}
    assert surveyed == expected, f"unsurveyed: {sorted(expected - surveyed)}"


def test_no_engine_currently_claims_technical_settlement() -> None:
    """Pin the truthful state. Every engine is `unsettled`, and the survey corroborates that none
    could be `settled` today -- because no engine has all six criteria measured, let alone satisfied.
    Declaring one would require the survey to corroborate it, which is the point."""
    rows = survey()
    declared = [r["engine"] for r in rows if r["declared_technical"] == "settled"]
    satisfiable = [r["engine"] for r in rows if r["technical_satisfiable"]]
    assert declared == [], f"an engine now claims technical settlement: {declared}"
    assert satisfiable == [], (
        f"the survey now corroborates a settlement: {satisfiable} -- if this is real, raise the "
        "settlement in the manifest AND cite the evidence; do not merely relax this test."
    )


def test_an_unmeasured_criterion_is_never_treated_as_satisfied() -> None:
    """The doctrine's whole point: absence of evidence is not evidence. Every run-required criterion
    is reported unmeasured, and a row carrying one must not be satisfiable."""
    rows = survey()

    def _has_unmeasured(row: dict) -> bool:
        criteria = row["criteria"]
        assert isinstance(criteria, dict)
        return any(v == UNMEASURED for v in criteria.values())

    unmeasured_but_satisfiable = [
        r["engine"] for r in rows if _has_unmeasured(r) and r["technical_satisfiable"]
    ]
    assert unmeasured_but_satisfiable == [], (
        f"{unmeasured_but_satisfiable}: a settlement was certified with an unmeasured criterion"
    )


def test_a_live_engine_has_a_resolvable_entry_point_and_collected_tests() -> None:
    """Every LIVE engine must at least clear the two criteria a survey can decide outright.

    `conforms` is excluded deliberately: three live engines are factories whose conformance is
    established by the agreement guard with stand-in arguments, and this survey reports `?` rather
    than re-deriving it. `?` is not a pass, so it is not asserted here.
    """
    from abraxas.engines.manifest import LIVE

    weak = [
        r["engine"]
        for r in survey()
        if r["status"] == LIVE
        and (
            r["criteria"]["entry_point"] != PRESENT
            or r["criteria"]["collected_tests"] != PRESENT
        )
    ]
    assert weak == [], f"live engines failing an inspectable criterion: {weak}"


# --------------------------------------------------------------------------------------------
# Failure modes -- a guard nobody has seen fail is not known to be a guard
# --------------------------------------------------------------------------------------------


def test_a_settled_claim_without_corroboration_is_rejected() -> None:
    """Drive the enforcement link to fail. A `settled` declaration the survey cannot corroborate
    must be named, not tolerated."""
    rows = [
        _row("honest", "unsettled", False),
        _row("overclaimer", "settled", False),
        _row("corroborated", "settled", True),
    ]
    assert uncorroborated_settlements(rows) == ["overclaimer"]


def test_a_corroborated_settled_claim_is_accepted() -> None:
    """The positive control: the checker must not reject everything, or it would be vacuously
    'safe' -- and a guard that rejects all input enforces nothing."""
    rows = [_row("real", "settled", True), _row("other", "unsettled", False)]
    assert uncorroborated_settlements(rows) == []


def test_the_unsettled_majority_is_never_reported_as_a_violation() -> None:
    """Unsettled is the honest default, not an offence."""
    rows = [_row(f"e{i}", "unsettled", False) for i in range(5)]
    assert uncorroborated_settlements(rows) == []


# --------------------------------------------------------------------------------------------
# The instrument itself -- this survey shipped a bug that looked exactly like a finding
# --------------------------------------------------------------------------------------------


def test_collection_sees_parametrised_test_ids() -> None:
    """The bug this pins: the survey first grepped test FILE TEXT for the engine name and reported
    trutina as having no coverage -- while `test_live_engine_entry_point_resolves[trutina]` was
    passing. A parametrised id appears nowhere in the test's source text.

    That is the same error as the doctrine arc's first wrong claim (`grep weakest` returned nothing,
    so "no weakest-link rule exists here"): a name-based check in place of a mechanism-based one.
    Discovered through pytest's collection, the parametrised case counts.
    """
    ids = _collected_test_ids()
    assert ids, "collection returned no test ids -- the survey's instrument is broken"

    trutina_ids = [i for i in ids if "trutina" in i]
    assert trutina_ids, (
        "no collected id mentions trutina, yet parametrised tests for it pass. If collection is "
        "broken the survey silently reports `?` for everything, which looks like a real finding."
    )


def test_grep_would_have_missed_it() -> None:
    """The counterfactual, asserted rather than described: the name is genuinely absent from the
    test file that exercises it, so the old grep-based metric was not merely coarse -- it was wrong."""
    agreement_tests = (REPO / "tests" / "test_engine_manifest_agreement.py").read_text()
    assert "trutina" not in agreement_tests, (
        "if the literal name now appears in the test file, this counterfactual no longer holds -- "
        "pick another parametrised engine rather than deleting the test"
    )
    assert any("trutina" in i for i in _collected_test_ids())


# --------------------------------------------------------------------------------------------
# Execution harness -- failure modes and NON_CONTENT_FIELDS counterfactuals
# --------------------------------------------------------------------------------------------


class _FakeNonDeterministicProvider:
    """A provider that returns a DIFFERENT envelope on every call.

    This is a class (not an EvidenceProvider subclass) so it cannot be
    accidentally mistaken for a real engine.  Its ``produce_evidence``
    signature matches the real interface just enough for the harness.
    """

    call_count: int = 0

    def produce_evidence(self, request_id: str, claim: str, context, budget=None):
        from abraxas.evidence.contract import EvidenceEnvelope

        self.__class__.call_count += 1
        n = self.__class__.call_count
        return EvidenceEnvelope(
            engine="fake-nd",
            request_id=request_id,
            claim=f"call-{n}",  # varies every call
            provenance={"source": "fake-nd"},
        )


def test_non_deterministic_engine_reported_no() -> None:
    """An engine that returns a DIFFERENT result on each call must be reported
    ``determinism: no``.  The harness runs the engine twice on identical input;
    the fake varies its ``claim`` field, so the two runs will differ."""
    from abraxas.engines.execution_harness import _content_dict, run_once

    # Reset the class-level counter so the test is repeatable.
    _FakeNonDeterministicProvider.call_count = 0
    fake = _FakeNonDeterministicProvider()

    d1 = run_once(fake, "req-1", "Is this deterministic?", {})
    d2 = run_once(fake, "req-1", "Is this deterministic?", {})

    c1 = _content_dict(d1)
    c2 = _content_dict(d2)

    assert c1 != c2, (
        "the fake must produce different content on each call "
        "for the non-determinism test to be valid"
    )

    # The harness's measure function walks through _construct_engine,
    # but we can test the logic directly: the _content_dict comparison
    # is what drives the verdict.
    assert c1["claim"] != c2["claim"], (
        "the non-determinism must be in a content field, not metadata"
    )


class _FakeNoProvenanceProvider:
    """A provider that returns an envelope with empty provenance."""

    def produce_evidence(self, request_id: str, claim: str, context, budget=None):
        from abraxas.evidence.contract import EvidenceEnvelope

        return EvidenceEnvelope(
            engine="fake-np",
            request_id=request_id,
            claim=claim,
            provenance={},
        )


def test_missing_provenance_reported_no() -> None:
    """An engine whose ``provenance`` is empty must be reported ``provenance: no``."""
    from abraxas.engines.execution_harness import run_once

    fake = _FakeNoProvenanceProvider()
    d = run_once(fake, "req-1", "Does this carry provenance?", {})
    assert d.get("provenance") == {}, "the fake must have empty provenance for the test to be valid"


class _FakeDeterministicProvider:
    """A deterministic provider with non-empty provenance (positive control)."""

    def produce_evidence(self, request_id: str, claim: str, context, budget=None):
        from abraxas.evidence.contract import EvidenceEnvelope

        return EvidenceEnvelope(
            engine="fake-det",
            request_id=request_id,
            claim=claim,
            confidence=0.85,
            provenance={"source": "fake-det", "method": "test"},
        )


def test_deterministic_engine_with_provenance_reported_yes() -> None:
    """The positive control: a deterministic engine with provenance must be
    reported ``yes`` on both criteria.  A checker that reports ``no`` for
    everything is vacuously 'safe' -- this proves the harness can say yes."""
    from abraxas.engines.execution_harness import _content_dict, run_once

    fake = _FakeDeterministicProvider()

    d1 = run_once(fake, "req-1", "Is this deterministic?", {})
    d2 = run_once(fake, "req-1", "Is this deterministic?", {})

    c1 = _content_dict(d1)
    c2 = _content_dict(d2)

    assert c1 == c2, (
        "deterministic provider must produce identical content on both runs"
    )
    assert d1.get("provenance"), "provenance must be non-empty"
    assert d2.get("provenance"), "provenance must be non-empty"


def test_non_content_fields_exclusion_metadata_only_diff_compares_equal() -> None:
    """Two envelopes differing ONLY in ``timestamp`` / ``evidence_id`` /
    ``schema_version`` must compare EQUAL after ``_content_dict`` strips them.

    This is the counterfactual that proves the exclusion is scoped rather
    than a blanket 'ignore everything'."""
    from abraxas.engines.execution_harness import _content_dict

    d1 = {
        "claim": "same",
        "confidence": 0.9,
        "timestamp": "2024-01-01T00:00:00Z",
        "evidence_id": "id-aaa",
        "schema_version": "v1",
    }
    d2 = {
        "claim": "same",
        "confidence": 0.9,
        "timestamp": "2025-12-31T23:59:59Z",
        "evidence_id": "id-bbb",
        "schema_version": "v2",
    }

    assert d1 != d2, "raw dicts must differ for the counterfactual to be valid"
    assert _content_dict(d1) == _content_dict(d2), (
        "envelopes differing only in NON_CONTENT_FIELDS must compare equal; "
        "if timestamp/evidence_id/schema_version changes cause a mismatch, "
        "the exclusion is NOT scoped correctly"
    )


def test_non_content_fields_exclusion_content_diff_is_detected() -> None:
    """Two envelopes differing in a CONTENT field (e.g. ``claim``) must
    compare UNEQUAL even after ``_content_dict`` strips metadata.  Together
    with the metadata-only test above, this pair proves the exclusion is
    scoped: it ignores what it should, and catches what it must."""
    from abraxas.engines.execution_harness import _content_dict

    d1 = {
        "claim": "this engine is deterministic",
        "confidence": 0.9,
        "timestamp": "2024-01-01T00:00:00Z",
        "evidence_id": "id-aaa",
        "schema_version": "v1",
    }
    d2 = {
        "claim": "this engine is non-deterministic",  # content differs
        "confidence": 0.9,
        "timestamp": "2024-01-01T00:00:00Z",
        "evidence_id": "id-aaa",
        "schema_version": "v1",
    }

    assert _content_dict(d1) != _content_dict(d2), (
        "envelopes differing in a content field must compare UNEQUAL; "
        "if the exclusion strips so much that a content change is missed, "
        "the harness would label a genuinely non-deterministic engine as 'yes'"
    )


# --------------------------------------------------------------------------------------------
# The VERDICT itself: measure() must be exercised with a FAILING case
# --------------------------------------------------------------------------------------------
#
# Everything above tests `_content_dict` and the fakes; none of it calls `measure()`. That is the
# function that produces the verdict the survey actually prints. Without the tests below, `measure()`
# could return `determinism: "yes"` unconditionally and every earlier test would still pass -- while
# the survey reported a green column built on nothing. A comparison helper being correct does not make
# the verdict that consumes it correct, and only a failing case can tell the two apart.
#
# These drive the verdict through `_construct_engine`, the same seam `measure()` uses in production.


def test_measure_reports_no_for_a_non_deterministic_engine(monkeypatch) -> None:
    """`measure()` on a provider that varies each call must return determinism == 'no'."""
    from abraxas.engines import execution_harness as harness

    _FakeNonDeterministicProvider.call_count = 0
    monkeypatch.setattr(harness, "_construct_engine", lambda spec: _FakeNonDeterministicProvider())

    verdict = harness.measure("noesis")

    assert verdict["determinism"] == "no", (
        f"a provider that differs on every call must be reported non-deterministic; got {verdict}"
    )
    assert "non-deterministic" in verdict["reason"], (
        f"the failure must be explained, not merely flagged; got reason={verdict['reason']!r}"
    )


def test_measure_reports_no_for_an_engine_with_empty_provenance(monkeypatch) -> None:
    """`measure()` must flag empty provenance independently of the determinism verdict."""
    from abraxas.engines import execution_harness as harness

    monkeypatch.setattr(harness, "_construct_engine", lambda spec: _FakeNoProvenanceProvider())

    verdict = harness.measure("noesis")

    assert verdict["provenance"] == "no", f"empty provenance must be reported; got {verdict}"
    assert "provenance" in verdict["reason"], verdict


def test_measure_reports_yes_for_a_deterministic_engine(monkeypatch) -> None:
    """Positive control. A checker that answers 'no' to everything is vacuously safe and enforces
    nothing, so the pass path has to be demonstrated too."""
    from abraxas.engines import execution_harness as harness

    monkeypatch.setattr(harness, "_construct_engine", lambda spec: _FakeDeterministicProvider())

    verdict = harness.measure("noesis")

    assert verdict["determinism"] == "yes", verdict
    assert verdict["provenance"] == "yes", verdict
    assert verdict["canonical_artifacts"] == "yes", verdict
    assert verdict["reason"] == "", (
        f"a passing verdict should carry no complaint; got {verdict['reason']!r}"
    )


def test_measure_reports_no_when_construction_fails(monkeypatch) -> None:
    """A provider that cannot be built cannot be certified."""
    from abraxas.engines import execution_harness as harness

    def _boom(spec):
        raise RuntimeError("cannot construct")

    monkeypatch.setattr(harness, "_construct_engine", _boom)

    verdict = harness.measure("noesis")

    assert verdict["determinism"] == "no" and verdict["provenance"] == "no", verdict
    assert "construction failed" in verdict["reason"], verdict


def test_measure_stays_unmeasured_for_a_planned_engine() -> None:
    """A PLANNED engine must never be certified: its criteria are '?', not 'yes'."""
    from abraxas.engines import execution_harness as harness

    verdict = harness.measure("aether")  # planned, zero files

    assert verdict["determinism"] == "?", verdict
    assert verdict["provenance"] == "?", verdict
    assert verdict["canonical_artifacts"] == "?", verdict


def test_measure_leaves_replay_unmeasured_for_a_live_engine() -> None:
    """`replay` is honestly '?' -- it needs artifact persistence this harness does not own, and the
    survey's rule is that a '?' cannot support a settlement."""
    from abraxas.engines import execution_harness as harness

    assert harness.measure("noesis")["replay"] == "?"


# --------------------------------------------------------------------------------------------
# The survey table must not understate what is now known
# --------------------------------------------------------------------------------------------


def test_conformance_is_measured_for_factory_engines() -> None:
    """`?` means "not measurable without running it" -- the table's own legend.

    Three live engines are factories. Their conformance was reported `?` because the survey could not
    build them without guessing constructor arguments. The execution harness supplies a DEFINED
    stand-in, so building them is now a measurement rather than a guess. Reporting `?` after that
    capability existed would be a status the code no longer supports.
    """
    rows = {r["engine"]: r for r in survey()}

    for name in ("athanor", "oracle", "cypher"):
        criteria = rows[name]["criteria"]
        assert criteria["conforms"] != UNMEASURED, (
            f"{name} is a live factory whose conformance is measurable via the harness; "
            f"reporting '?' understates what is known"
        )
        assert criteria["conforms"] == PRESENT, (name, criteria)


def test_only_replay_remains_unmeasured_for_live_engines() -> None:
    """Pin the honest state: the gap between the live engines and a technical settlement is exactly
    ONE criterion, and it is named. If this list grows, something regressed; if it shrinks, an engine
    may be settleable and the manifest should say so with cited evidence."""
    for row in survey():
        if row["status"] != "live":
            continue
        unmeasured = sorted(k for k, v in row["criteria"].items() if v == UNMEASURED)
        assert unmeasured == ["replay"], (
            f"{row['engine']}: unmeasured criteria are {unmeasured}, expected exactly ['replay']. "
            "Either a measurement was lost, or replay became measurable -- in which case raise the "
            "settlement in the manifest and cite the evidence rather than editing this test."
        )
