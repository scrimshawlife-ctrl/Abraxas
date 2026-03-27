from __future__ import annotations

CLOSURE_STATES = {
    "CLOSURE_COMPLETE",
    "CLOSURE_COMPLETE_WITH_WAIVERS",
    "PARTIALLY_CLOSED",
    "BLOCKED",
    "DEGRADED",
    "NOT_COMPUTABLE",
}


def classify_domain_closure_state(blockers: list[str], waived_blockers: list[str]) -> str:
    if not blockers:
        return "CLOSURE_COMPLETE"
    unwaived = sorted(set(blockers) - set(waived_blockers))
    if not unwaived:
        return "CLOSURE_COMPLETE_WITH_WAIVERS"
    if any("stale" in x for x in unwaived):
        return "DEGRADED"
    return "BLOCKED"


def classify_system_closure_state(domain_states: dict[str, str], dependency_states: dict[str, str]) -> str:
    if not domain_states:
        return "NOT_COMPUTABLE"
    states = set(domain_states.values())
    dep_states = set(dependency_states.values())
    if "NOT_COMPUTABLE" in states or "NOT_COMPUTABLE" in dep_states:
        return "NOT_COMPUTABLE"
    if "BLOCKED" in states or "DEPENDENCY_BLOCKED" in dep_states:
        return "BLOCKED"
    if "DEGRADED" in states:
        return "DEGRADED"
    if "CLOSURE_COMPLETE_WITH_WAIVERS" in states:
        return "CLOSURE_COMPLETE_WITH_WAIVERS"
    if states == {"CLOSURE_COMPLETE"}:
        return "CLOSURE_COMPLETE"
    return "PARTIALLY_CLOSED"
