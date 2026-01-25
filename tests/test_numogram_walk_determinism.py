from __future__ import annotations

from abraxas_ase.sdct.numogram.spec_v1 import build_default_graph_v1
from abraxas_ase.sdct.numogram.walk import walk


def test_numogram_walk_determinism() -> None:
    graph = build_default_graph_v1()
    walk_a = walk(graph, "event-a", "2026-01-24", "", steps=24)
    walk_b = walk(graph, "event-a", "2026-01-24", "", steps=24)
    walk_c = walk(graph, "event-b", "2026-01-24", "", steps=24)

    assert walk_a == walk_b
    assert walk_a != walk_c
