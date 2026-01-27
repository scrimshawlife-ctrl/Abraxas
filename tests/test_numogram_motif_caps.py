from __future__ import annotations

from abraxas_ase.sdct.domains.numogram_motif import NumogramMotifCartridge
from abraxas_ase.sdct.numogram.spec_v1 import build_default_graph_v1


def test_numogram_motif_caps() -> None:
    graph = build_default_graph_v1()
    cartridge = NumogramMotifCartridge(graph=graph, max_motifs=10, steps=40)
    sym = ["a", "b", "c", "d", "e", "f", "g", "a", "b", "c", "d", "e", "f", "g"] * 3
    motifs = cartridge.extract_motifs(sym)

    assert len(motifs) == 10
    assert [m.motif_id for m in motifs] == sorted([m.motif_id for m in motifs])
