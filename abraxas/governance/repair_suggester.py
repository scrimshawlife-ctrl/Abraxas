"""PATCH-004 read-only repair suggestions."""

from __future__ import annotations

from typing import Dict, List


CONFIDENCE_MAP = {
    "MISSING_PATH": 1.0,
    "PARTIAL": 0.6,
    "NOT_COMPUTABLE": 0.2,
}


def suggest_repairs(validation_report: Dict[str, object]) -> Dict[str, object]:
    suggestions: List[Dict[str, object]] = []

    for subsystem in validation_report.get("subsystems", []):
        state = subsystem.get("status", "NOT_COMPUTABLE")
        if state not in {"MISSING_PATH", "PARTIAL", "NOT_COMPUTABLE"}:
            continue

        if state == "MISSING_PATH":
            action = "CREATE_MINIMAL_MODULE"
        elif state == "PARTIAL":
            action = "ADD_TEST"
        else:
            action = "INSPECT_BRANCH"

        suggestions.append(
            {
                "component_id": subsystem.get("id", "NOT_COMPUTABLE"),
                "issue": state,
                "suggested_action": action,
                "confidence": CONFIDENCE_MAP[state],
            }
        )

    suggestions = sorted(suggestions, key=lambda item: item["component_id"])

    status = "PASS"
    if any(suggestion["issue"] == "MISSING_PATH" for suggestion in suggestions):
        status = "FAIL"
    elif suggestions:
        status = "PARTIAL"

    return {
        "schema_version": "RepairSuggestionReport.v1",
        "status": status,
        "read_only": True,
        "suggestions": suggestions,
    }
