from __future__ import annotations

from abx.lineage.derivationClassification import classify_derivation
from abx.lineage.lineageClassification import classify_lineage
from abx.lineage.lineageReports import build_lineage_report
from abx.lineage.lineageScorecardSerialization import serialize_lineage_scorecard
from abx.lineage.mutationClassification import classify_mutation
from abx.lineage.mutationReports import build_mutation_report
from abx.lineage.provenanceReports import build_provenance_report
from abx.lineage.transitionReports import build_provenance_transition_report
from abx.lineage.lineageScorecard import build_lineage_governance_scorecard


def test_lineage_governance_determinism() -> None:
    report_a = build_lineage_report()
    report_b = build_lineage_report()
    assert report_a == report_b
    assert set(report_a["lineageStates"].values()).issubset(
        {
            "SOURCE_TRACEABLE_STATE",
            "DERIVED_WITH_VALID_LINEAGE",
            "MERGED_LINEAGE_STATE",
            "COPIED_LINEAGE_STATE",
            "CACHED_LINEAGE_STATE",
            "MATERIALIZED_LINEAGE_STATE",
            "PROVENANCE_BROKEN",
            "NOT_COMPUTABLE",
        }
    )
    assert classify_lineage(lineage_kind="PRIMARY", source_ref="ingest/x") == "SOURCE_TRACEABLE_STATE"
    assert classify_lineage(lineage_kind="UNKNOWN", source_ref="ingest/x") == "NOT_COMPUTABLE"
    assert any(x["code"] == "LINEAGE_NOT_COMPUTABLE" for x in report_a["governanceErrors"])


def test_provenance_derivation_determinism() -> None:
    report_a = build_provenance_report()
    report_b = build_provenance_report()
    assert report_a == report_b
    assert set(x["derivation_state"] for x in report_a["derivations"]).issubset(
        {"DERIVATION_VALID", "DERIVATION_UNKNOWN", "STALE_DERIVED_STATE", "NOT_COMPUTABLE"}
    )
    assert classify_derivation(provenance_state="PROVENANCE_STALE", transform_chain="agg") == "STALE_DERIVED_STATE"
    assert classify_derivation(provenance_state="NOT_COMPUTABLE", transform_chain="") == "NOT_COMPUTABLE"
    assert any(x["severity"] == "ERROR" for x in report_a["governanceErrors"])


def test_mutation_legitimacy_determinism() -> None:
    report_a = build_mutation_report()
    report_b = build_mutation_report()
    assert report_a == report_b
    assert set(report_a["mutationStates"].values()).issubset(
        {"MUTATION_LEGITIMATE", "MUTATION_CONDITIONAL", "MUTATION_ILLEGITIMATE", "UNAUTHORIZED_MUTATION", "BLOCKED"}
    )
    assert classify_mutation(legitimacy_state="MUTATION_LEGITIMATE", authority_state="AUTHORIZED", replay_state="REPLAYABLE_STATE") == "MUTATION_LEGITIMATE"
    assert classify_mutation(legitimacy_state="MUTATION_CONDITIONAL", authority_state="BLOCKED", replay_state="NON_REPLAYABLE_STATE") == "BLOCKED"


def test_provenance_transition_determinism() -> None:
    report_a = build_provenance_transition_report()
    report_b = build_provenance_transition_report()
    assert report_a == report_b
    assert {x["to_state"] for x in report_a["transitions"]}.issuperset(
        {"PROVENANCE_STALE", "STALE_DERIVED_STATE", "UNAUTHORIZED_MUTATION", "NON_REPLAYABLE_STATE", "BLOCKED"}
    )
    assert any(x["action_required"] == "RE_DERIVATION_REQUIRED" for x in report_a["transitions"])


def test_lineage_scorecard_determinism_and_blockers() -> None:
    score_a = build_lineage_governance_scorecard()
    score_b = build_lineage_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "LINEAGE_GOVERNED",
        "STALE_DERIVED_BURDENED",
        "PROVENANCE_BROKEN_BURDENED",
        "BLOCKED",
        "PARTIAL",
        "NOT_COMPUTABLE",
    }
    assert "mutation_legitimacy_quality" in score_a.dimensions
    assert "source_traceability_clarity" in score_a.blockers
    serialized = serialize_lineage_scorecard(score_a)
    assert serialized == serialize_lineage_scorecard(score_b)


def test_elegance_regressions_and_invariance_guards() -> None:
    lineage = build_lineage_report()
    provenance = build_provenance_report()
    mutation = build_mutation_report()
    transitions = build_provenance_transition_report()

    assert len(set(lineage["lineageStates"].values())) <= 8
    assert len(set(mutation["mutationStates"].values())) <= 5
    if any(x["unauthorized_state"] == "UNAUTHORIZED_MUTATION" for x in transitions["unauthorized"]):
        assert any(v == "UNAUTHORIZED_MUTATION" for v in mutation["mutationStates"].values())
    assert any(x["stale_state"] == "YES" for x in provenance["derivations"])
    assert all(error["code"].startswith(("LINEAGE_", "PROVENANCE_", "MUTATION_")) for error in lineage["governanceErrors"] + provenance["governanceErrors"] + mutation["governanceErrors"])
