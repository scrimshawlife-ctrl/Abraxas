from __future__ import annotations

from abraxas_ase.sdct.domains.digit_motif import DigitMotifCartridge


def test_digit_motif_extraction() -> None:
    item = {
        "id": "1",
        "source": "alpha",
        "published_at": "2026-01-24T00:00:00Z",
        "title": "UFC 311",
        "text": "UFC 311 at 7-11 on 2026-01-24",
    }
    cartridge = DigitMotifCartridge()
    sym = cartridge.encode(item)
    motifs = cartridge.extract_motifs(sym)
    motif_texts = [m.motif_text for m in motifs]

    assert "7" in motif_texts
    assert "11" in motif_texts
    assert "711" in motif_texts
    assert "2026" in motif_texts
    assert "0124" in motif_texts
    assert [m.motif_id for m in motifs] == sorted([m.motif_id for m in motifs])
