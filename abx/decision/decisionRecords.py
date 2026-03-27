from __future__ import annotations

from abx.governance.decision_types import DecisionOutcomeRecord, DecisionRecord


def build_decision_records(run_id: str = "RUN-DECISION") -> list[DecisionRecord]:
    rows = [
        DecisionRecord(
            decision_id="decision.input.acceptance",
            run_id=run_id,
            policy_refs=["policy.boundary.validation", "policy.boundary.trust"],
            value_refs=["value.determinism", "value.provenance"],
            evidence_refs=["BoundaryValidationReport.v1", "BoundaryTrustReport.v1"],
            trust_state="EXTERNAL_ASSERTED",
            context_ref="boundary/input",
            outcome=DecisionOutcomeRecord(
                outcome="DEGRADED",
                completeness="fully_governed",
                alternatives_rejected=["ACCEPT", "REJECT"],
            ),
        ),
        DecisionRecord(
            decision_id="decision.scheduler.order",
            run_id=run_id,
            policy_refs=["policy.runtime.ordering"],
            value_refs=["value.determinism"],
            evidence_refs=["ScaleSchedulerInspectionArtifact.v1"],
            trust_state="AUTHORITATIVE_INTERNAL",
            context_ref="runtime/scheduler",
            outcome=DecisionOutcomeRecord(
                outcome="ACCEPT",
                completeness="fully_governed",
                alternatives_rejected=["HEURISTIC_ORDER"],
            ),
        ),
        DecisionRecord(
            decision_id="decision.degradation.route",
            run_id=run_id,
            policy_refs=["policy.resilience.degradation"],
            value_refs=["value.containment"],
            evidence_refs=["DegradationStateRecord.v1"],
            trust_state="GOVERNED_DERIVED",
            context_ref="resilience/degradation",
            outcome=DecisionOutcomeRecord(
                outcome="DEGRADED",
                completeness="partially_governed",
                alternatives_rejected=["FULL", "BLOCKED"],
            ),
        ),
    ]
    return sorted(rows, key=lambda x: x.decision_id)
