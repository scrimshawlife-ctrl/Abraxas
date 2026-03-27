from __future__ import annotations

from typing import Iterable, Mapping


def stable_sort_score_desc_id_asc(items: Iterable[Mapping[str, object]]) -> list[dict[str, object]]:
    """Deterministic stable sort: score DESC then id ASC."""

    normalized = [dict(item) for item in items]
    return sorted(
        normalized,
        key=lambda item: (-float(item.get("score", 0.0)), str(item.get("id", ""))),
    )


def normalize_vector(vector: Mapping[str, float]) -> dict[str, float]:
    """Normalize input vector to [0.0, 1.0] and deterministic key ordering."""

    if not vector:
        return {}
    keys = sorted(vector.keys())
    values = [float(vector[k]) for k in keys]
    v_min, v_max = min(values), max(values)
    if v_max == v_min:
        return {k: 0.0 for k in keys}
    return {k: (float(vector[k]) - v_min) / (v_max - v_min) for k in keys}
