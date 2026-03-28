from __future__ import annotations


def classify_mutation(*, legitimacy_state: str, authority_state: str, replay_state: str) -> str:
    if authority_state == "BLOCKED":
        return "BLOCKED"
    if legitimacy_state == "MUTATION_ILLEGITIMATE" or authority_state == "UNAUTHORIZED_MUTATION":
        return "UNAUTHORIZED_MUTATION"
    if replay_state == "NON_REPLAYABLE_STATE":
        return "MUTATION_CONDITIONAL"
    if legitimacy_state == "MUTATION_LEGITIMATE":
        return "MUTATION_LEGITIMATE"
    return "MUTATION_ILLEGITIMATE"
