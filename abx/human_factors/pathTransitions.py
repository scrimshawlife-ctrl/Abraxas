from __future__ import annotations

from abx.human_factors.operatorPaths import build_operator_paths


def build_path_transitions() -> list[dict[str, str]]:
    transitions: list[dict[str, str]] = []
    for row in build_operator_paths():
        transitions.append(
            {
                "path_id": row.path_id,
                "from_condition": row.condition,
                "to_surface": row.next_surface,
                "recovery_link": row.recovery_link,
            }
        )
    return sorted(transitions, key=lambda x: x["path_id"])
