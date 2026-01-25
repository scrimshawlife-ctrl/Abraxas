from __future__ import annotations

from abraxas_ase.sdct.numogram.spec_v1 import build_default_graph_v1, validate_graph


def test_numogram_graph_validity() -> None:
    graph = build_default_graph_v1()
    validate_graph(graph)
