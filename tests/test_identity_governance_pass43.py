from __future__ import annotations

from abx.identity.coherenceClassification import classify_coherence
from abx.identity.coherenceReports import build_referential_coherence_report
from abx.identity.identityClassification import classify_identity_resolution
from abx.identity.identityReports import build_identity_resolution_report
from abx.identity.identityScorecard import build_identity_governance_scorecard
from abx.identity.identityScorecardSerialization import serialize_identity_scorecard
from abx.identity.persistenceClassification import classify_persistence
from abx.identity.persistenceReports import build_entity_persistence_report
from abx.identity.transitionReports import build_identity_transition_report


def test_identity_resolution_determinism_and_classes() -> None:
    report_a = build_identity_resolution_report()
    report_b = build_identity_resolution_report()
    assert report_a == report_b
    assert set(report_a["identityStates"].values()).issuperset(
        {
            "CANONICAL_IDENTITY_RESOLVED",
            "ALIAS_RESOLVED",
            "FOREIGN_REFERENCE_RESOLVED",
            "TRANSIENT_HANDLE_RESOLVED",
            "REFERENCE_AMBIGUOUS",
            "UNRESOLVED_REFERENCE",
        }
    )
    assert classify_identity_resolution(resolution_state="ALIAS_RESOLVED", canonical_entity="ent.account.001") == "ALIAS_RESOLVED"


def test_entity_persistence_determinism_and_classes() -> None:
    report_a = build_entity_persistence_report()
    report_b = build_entity_persistence_report()
    assert report_a == report_b
    assert set(report_a["persistenceStates"].values()).issuperset(
        {
            "PERSISTENT_CANONICAL_IDENTITY",
            "REMAPPED_CANONICAL_IDENTITY",
            "DEPRECATED_IDENTIFIER",
            "DISPLAY_ALIAS_ONLY",
            "IMPORTED_IDENTITY_SHADOW",
            "IDENTITY_BREAK",
        }
    )
    assert classify_persistence(persistence_state="DISPLAY_ALIAS_ONLY", continuity_ref="cont/x") == "DISPLAY_ALIAS_ONLY"


def test_referential_coherence_determinism_and_merge_split() -> None:
    report_a = build_referential_coherence_report()
    report_b = build_referential_coherence_report()
    assert report_a == report_b
    assert set(report_a["coherenceStates"].values()).issuperset(
        {
            "REFERENTIALLY_COHERENT",
            "ALIAS_ACTIVE_COHERENT",
            "MERGE_ACTIVE_COHERENT",
            "SPLIT_ACTIVE_COHERENT",
            "DUPLICATE_ENTITY_SUSPECTED",
            "DUPLICATE_ENTITY_CONFIRMED",
        }
    )
    assert classify_coherence(coherence_state="UNKNOWN", downstream_state="DOWNSTREAM_CONFLICT") == "DUPLICATE_ENTITY_SUSPECTED"


def test_identity_transition_determinism() -> None:
    report_a = build_identity_transition_report()
    report_b = build_identity_transition_report()
    assert report_a == report_b
    assert {x["mismatch_state"] for x in report_a["mismatch"]}.issuperset(
        {
            "DUPLICATE_SUSPECTED",
            "DUPLICATE_CONFIRMED",
            "REFERENCE_MISMATCH_ACTIVE",
            "DEPRECATED_IDENTIFIER_ACTIVE",
            "REMAP_REQUIRED",
            "CANONICAL_REFERENCE_RESTORED",
        }
    )


def test_identity_scorecard_determinism_and_blockers() -> None:
    score_a = build_identity_governance_scorecard()
    score_b = build_identity_governance_scorecard()
    assert score_a == score_b
    assert score_a.category in {
        "IDENTITY_GOVERNED",
        "DUPLICATE_BURDENED",
        "MISMATCH_BURDENED",
        "PARTIAL",
        "BLOCKED",
        "NOT_COMPUTABLE",
    }
    assert "reference_mismatch_visibility" in score_a.blockers
    assert serialize_identity_scorecard(score_a) == serialize_identity_scorecard(score_b)


def test_elegance_regression_guards() -> None:
    identity = build_identity_resolution_report()
    persistence = build_entity_persistence_report()
    coherence = build_referential_coherence_report()

    assert len(set(identity["identityStates"].values())) <= 6
    assert len(set(persistence["persistenceStates"].values())) <= 6
    assert any(x["merge_state"] == "MERGE_ILLEGITIMATE" for x in coherence["merge"])
    assert any(x["code"] == "COHERENCE_FAIL" for x in coherence["governanceErrors"])
