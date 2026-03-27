from __future__ import annotations

from abx.lineage.mutationClassification import classify_mutation
from abx.lineage.mutationLegitimacyRecords import build_mutation_legitimacy_records
from abx.lineage.types import MutationAuthorityRecord, ReplayabilityRecord
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def build_mutation_report() -> dict[str, object]:
    rows = build_mutation_legitimacy_records()
    authority = tuple(
        MutationAuthorityRecord(
            authority_id=f"auth.{x.legitimacy_id}",
            legitimacy_id=x.legitimacy_id,
            authority_scope="state_mutation",
            authority_state="AUTHORIZED" if x.legitimacy_state != "MUTATION_ILLEGITIMATE" else "UNAUTHORIZED_MUTATION",
        )
        for x in rows
    )
    replay = tuple(
        ReplayabilityRecord(
            replay_id=f"replay.{x.legitimacy_id}",
            state_ref=x.state_ref,
            replay_state="REPLAYABLE_STATE" if x.legitimacy_state != "MUTATION_ILLEGITIMATE" else "NON_REPLAYABLE_STATE",
            reconstructable_state="RECONSTRUCTABLE" if x.legitimacy_state != "MUTATION_ILLEGITIMATE" else "NON_RECONSTRUCTABLE",
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
    report = {
        "artifactType": "MutationLegitimacyAudit.v1",
        "artifactId": "mutation-legitimacy-audit",
        "mutations": [x.__dict__ for x in rows],
        "authority": [x.__dict__ for x in authority],
        "replayability": [x.__dict__ for x in replay],
        "mutationStates": mutation_states,
    }
    report["auditHash"] = sha256_bytes(dumps_stable(report).encode("utf-8"))
    return report
