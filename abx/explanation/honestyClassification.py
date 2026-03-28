from __future__ import annotations


def classify_honesty(*, honesty_state: str, causal_state: str, support_state: str, omission_state: str) -> str:
    if honesty_state in {"NOT_COMPUTABLE", "BLOCKED"} or omission_state == "NOT_COMPUTABLE":
        return "NOT_COMPUTABLE"
    if honesty_state == "UNSUPPORTED_EXPLANATORY_JUMP":
        return "UNSUPPORTED_EXPLANATORY_JUMP"
    if causal_state == "CAUSAL_LANGUAGE_USED" and support_state in {"INSUFFICIENT", "AMBIGUOUS"}:
        return "CAUSAL_OVERREACH_RISK"
    if honesty_state == "CAVEAT_OMISSION_RISK" or omission_state == "CAVEAT_OMISSION_RISK":
        return "CAVEAT_OMISSION_RISK"
    if honesty_state == "EXPLANATION_SMOOTHING_RISK":
        return "EXPLANATION_SMOOTHING_RISK"
    if honesty_state == "INTERPRETIVELY_COMPRESSED_BUT_HONEST":
        return "INTERPRETIVELY_COMPRESSED_BUT_HONEST"
    return "INTERPRETIVELY_HONEST"
