from __future__ import annotations

from abx.resilience.faultInjection import plan_fault_injection
from abx.resilience.types import DegradationStateRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable

_STATE_ORDER = ["FULL", "DEGRADED", "LIMITED", "BLOCKED"]


_MODE_TO_STATE = {
    "VALIDATION_FAILURE": "LIMITED",
    "INVARIANT_BREAK": "BLOCKED",
    "SCHEDULER_DISRUPTION": "DEGRADED",
    "MISSING_ARTIFACT": "LIMITED",
    "DELAYED_PARTIAL_EXECUTION": "DEGRADED",
}


def _max_state(states: list[str]) -> str:
    if not states:
        return "FULL"
    return sorted(states, key=lambda x: _STATE_ORDER.index(x))[-1]


def evaluate_degradation(scenario_id: str, subsystem: str = "system") -> DegradationStateRecord:
    fault = plan_fault_injection(scenario_id=scenario_id)
    states = [_MODE_TO_STATE.get(step["mode"], "DEGRADED") for step in fault.injection_plan]
    state = _max_state(states)

    fallback_actions = {
        "FULL": ["proceed-full-runbook"],
        "DEGRADED": ["skip-non-critical-steps", "emit-partial-results"],
        "LIMITED": ["contain-to-core-workflow", "emit-partial-results", "open-incident-record"],
        "BLOCKED": ["halt-safely", "open-incident-record", "execute-recovery-drill"],
    }[state]
    emitted_artifacts = [
        "FaultInjectionArtifact.v1",
        "DegradationStateRecord.v1",
        "RecoveryDrillArtifact.v1" if state in {"LIMITED", "BLOCKED"} else "RunbookExecutionSummary.v1",
    ]

    rationale = f"state derived from deterministic injection plan with {len(fault.injection_plan)} injected surfaces"
    payload = {
        "scenario_id": scenario_id,
        "subsystem": subsystem,
        "state": state,
        "fallback_actions": fallback_actions,
        "emitted_artifacts": emitted_artifacts,
        "rationale": rationale,
    }
    state_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))

    return DegradationStateRecord(
        artifact_type="DegradationStateRecord.v1",
        artifact_id=f"degradation-state-{subsystem}-{scenario_id}",
        scenario_id=scenario_id,
        subsystem=subsystem,
        state=state,
        fallback_actions=fallback_actions,
        emitted_artifacts=emitted_artifacts,
        rationale=rationale,
        state_hash=state_hash,
    )


def render_degradation_report(scenario_id: str, subsystem: str = "system") -> dict[str, object]:
    artifact = evaluate_degradation(scenario_id=scenario_id, subsystem=subsystem)
    return {
        "artifactType": artifact.artifact_type,
        "artifactId": artifact.artifact_id,
        "scenarioId": artifact.scenario_id,
        "subsystem": artifact.subsystem,
        "state": artifact.state,
        "fallbackActions": artifact.fallback_actions,
        "emittedArtifacts": artifact.emitted_artifacts,
        "rationale": artifact.rationale,
        "stateHash": artifact.state_hash,
    }
