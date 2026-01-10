from __future__ import annotations
from abraxas.overlays.registry import OverlayRegistry


def test_registry_default_contains_overlays():
    r = OverlayRegistry.default()
    assert r.get("aalmanac").meta.name == "aalmanac"
    assert r.get("beatoven").meta.name == "beatoven"
    assert r.get("neon_genie").meta.name == "neon_genie"
