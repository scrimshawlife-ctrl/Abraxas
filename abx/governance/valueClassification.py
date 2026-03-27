from __future__ import annotations

from abx.governance.valueModel import build_value_model


def classify_values() -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in build_value_model():
        grouped.setdefault(row.status, []).append(row.value_id)
    return {k: sorted(v) for k, v in sorted(grouped.items())}


def detect_overlapping_value_terms() -> list[str]:
    seen: dict[str, str] = {}
    overlaps: list[str] = []
    for row in build_value_model():
        key = row.value_term.replace("_", "")
        if key in seen:
            overlaps.append(f"{seen[key]}::{row.value_id}")
        else:
            seen[key] = row.value_id
    return sorted(overlaps)
