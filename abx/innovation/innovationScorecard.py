from __future__ import annotations

from abx.innovation.experimentReports import build_experiment_audit_report
from abx.innovation.lifecycleReports import build_innovation_lifecycle_audit_report
from abx.innovation.portfolioReports import build_innovation_portfolio_audit_report
from abx.innovation.researchReports import build_research_artifact_audit_report
from abx.innovation.types import ExperimentationGovernanceScorecard
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_experimentation_governance_scorecard() -> ExperimentationGovernanceScorecard:
    experiment = build_experiment_audit_report()
    research = build_research_artifact_audit_report()
    lifecycle = build_innovation_lifecycle_audit_report()
    portfolio = build_innovation_portfolio_audit_report()

    dimensions = {
        "experimentation_surface_clarity": "PARTIAL" if experiment["unowned"] else "GOVERNED",
        "sandbox_boundary_quality": "PARTIAL" if experiment["hiddenInfluence"] else "GOVERNED",
        "hypothesis_artifact_discipline": "GOVERNED" if research["hypotheses"] and research["conditions"] else "NOT_COMPUTABLE",
        "research_comparability_quality": "GOVERNED" if research["comparability"]["promotable"] else "PARTIAL",
        "lifecycle_clarity": "GOVERNED" if not lifecycle["redundantGrammar"] else "PARTIAL",
        "promotion_readiness_visibility": "PARTIAL" if any(x["missing_evidence"] for x in lifecycle["promotionReadiness"]) else "GOVERNED",
        "retirement_discipline": "PARTIAL" if not portfolio["retirement"] else "GOVERNED",
        "stale_experiment_burden": "PARTIAL" if portfolio["stale"] else "GOVERNED",
        "portfolio_signal_to_noise": "PARTIAL" if portfolio["classification"]["low_value"] else "GOVERNED",
        "operator_legibility_of_experimental_state": "MONITORED",
    }
    blockers = sorted(k for k, v in dimensions.items() if v in {"PARTIAL", "NOT_COMPUTABLE", "UNBOUNDED"})
    evidence = {
        "experiment": [experiment["auditHash"]],
        "research": [research["auditHash"]],
        "lifecycle": [lifecycle["auditHash"]],
        "portfolio": [portfolio["auditHash"]],
        "unownedExperiments": experiment["unowned"],
        "staleExperiments": [x["experimentId"] for x in portfolio["stale"]],
    }
    digest = sha256_bytes(dumps_stable({"dimensions": dimensions, "evidence": evidence, "blockers": blockers}).encode("utf-8"))
    return ExperimentationGovernanceScorecard(
        artifact_type="ExperimentationGovernanceScorecard.v1",
        artifact_id="experimentation-governance-scorecard",
        dimensions=dimensions,
        evidence=evidence,
        blockers=blockers,
        scorecard_hash=digest,
    )
