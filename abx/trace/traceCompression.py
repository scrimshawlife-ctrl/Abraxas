from __future__ import annotations

from abx.observability.types import CausalTraceRecord


def compress_trace(records: list[CausalTraceRecord]) -> list[str]:
    compressed: list[str] = []
    for row in records:
        compressed.append(f"{row.step}>{row.evidence_ref}:{row.state}")
    return compressed
