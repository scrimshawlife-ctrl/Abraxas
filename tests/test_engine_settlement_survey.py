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
