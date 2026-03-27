from __future__ import annotations

from abx.human_factors.operatorPaths import build_operator_paths


def classify_operator_paths() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"canonical": [], "adapted": [], "fragmented": [], "legacy": [], "not_computable": []}
    for row in build_operator_paths():
        key = row.path_state if row.path_state in out else "not_computable"
        out[key].append(row.path_id)
    return {k: sorted(v) for k, v in out.items()}
