from __future__ import annotations

from abx.lineage.mutationClassification import classify_mutation
from abx.lineage.mutationLegitimacyRecords import build_mutation_legitimacy_records
from abx.lineage.types import LineageGovernanceErrorRecord, MutationAuthorityRecord, ReplayabilityRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_mutation_report() -> dict[str, object]:
    rows = build_mutation_legitimacy_records()
    authority = tuple(
        MutationAuthorityRecord(
            authority_id=f"auth.{x.legitimacy_id}",
            legitimacy_id=x.legitimacy_id,
            authority_scope=x.mutation_scope,
            authority_state="UNAUTHORIZED_MUTATION"
            if x.legitimacy_state == "MUTATION_ILLEGITIMATE"
            else ("BLOCKED" if x.actor.startswith("manual.") else "AUTHORIZED"),
            policy_ref=x.authority_ref,
        )
        for x in rows
    )
    replay = tuple(
        ReplayabilityRecord(
            replay_id=f"replay.{x.legitimacy_id}",
            state_ref=x.state_ref,
            replay_state="NON_REPLAYABLE_STATE"
            if x.legitimacy_state == "MUTATION_ILLEGITIMATE"
            else ("NON_REPLAYABLE_STATE" if x.actor.startswith("manual.") else "REPLAYABLE_STATE"),
            reconstructable_state="NON_RECONSTRUCTABLE"
            if x.legitimacy_state == "MUTATION_ILLEGITIMATE"
            else ("NON_RECONSTRUCTABLE" if x.actor.startswith("manual.") else "RECONSTRUCTABLE"),
            replay_basis="DELTA_LOG_AND_SOURCE_SNAPSHOT"
            if x.legitimacy_state == "MUTATION_LEGITIMATE"
            else ("MISSING_APPROVAL_CHAIN" if x.actor.startswith("manual.") else "PARTIAL_DELTA_LOG"),
        )
        for x in rows
    )
    replay_by_state = {x.state_ref: x for x in replay}
    authority_by_leg = {x.legitimacy_id: x for x in authority}
    mutation_states = {
        x.legitimacy_id: classify_mutation(
            legitimacy_state=x.legitimacy_state,
            authority_state=authority_by_leg[x.legitimacy_id].authority_state,
            replay_state=replay_by_state[x.state_ref].replay_state,
        )
        for x in rows
    }
    errors = []
    for row in rows:
        state = mutation_states[row.legitimacy_id]
        if state in {"UNAUTHORIZED_MUTATION", "BLOCKED"}:
            errors.append(
                LineageGovernanceErrorRecord(
                    code="MUTATION_TRUST_DOWNGRADE",
                    severity="ERROR",
                    message=f"{row.state_ref} mutation state={state} actor={row.actor}",
                )
            )
    report = {
        "artifactType": "MutationLegitimacyAudit.v1",
        "artifactId": "mutation-legitimacy-audit",
        "mutations": [x.__dict__ for x in rows],
        "authority": [x.__dict__ for x in authority],
        "replayability": [x.__dict__ for x in replay],
        "mutationStates": mutation_states,
        "governanceErrors": [x.__dict__ for x in errors],
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
