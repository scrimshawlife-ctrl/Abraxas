from __future__ import annotations

from abraxas_ase.sdct.domains.square_constraints import SquareConstraintCartridge


def test_square_motif_caps() -> None:
    item = {
        "id": "1",
        "source": "alpha",
        "published_at": "2026-01-24T00:00:00Z",
        "title": "Alpha Beta Gamma Delta Epsilon Zeta Eta Theta Iota Kappa Lambda",
        "text": "1234567890" * 10,
    }
    cartridge = SquareConstraintCartridge(max_motifs=10)
    sym = cartridge.encode(item)
    motifs = cartridge.extract_motifs(sym)

    assert len(motifs) == 10
    assert [m.motif_id for m in motifs] == sorted([m.motif_id for m in motifs])
