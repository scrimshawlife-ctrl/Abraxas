from __future__ import annotations

from pathlib import Path
from typing import Iterable, TypedDict


class CorrelationPointerBlock(TypedDict):
    correlation_pointers: list[str]
    correlation_pointer_state: str
    correlation_pointer_unresolved_reasons: list[str]


def _append_unique(target: list[str], seen: set[str], value: str) -> None:
    if value in seen:
        return
    target.append(value)
    seen.add(value)


def build_correlation_pointer_block(
    *,
    root: Path,
    paths: Iterable[Path] = (),
    anchors: Iterable[str] = (),
) -> CorrelationPointerBlock:
    pointers: list[str] = []
    unresolved_reasons: list[str] = []
    seen: set[str] = set()

    for path in paths:
        rel_path = str(path.relative_to(root))
        if path.exists():
            _append_unique(pointers, seen, rel_path)
        else:
            unresolved_reasons.append(f"artifact_missing:{rel_path}")

    for anchor in anchors:
        _append_unique(pointers, seen, anchor)

    pointer_state = "present" if pointers else "empty"
    if unresolved_reasons:
        pointer_state = "unresolved"

    return CorrelationPointerBlock(
        correlation_pointers=pointers,
        correlation_pointer_state=pointer_state,
        correlation_pointer_unresolved_reasons=unresolved_reasons,
    )
