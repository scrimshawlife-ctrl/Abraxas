from __future__ import annotations

from abraxas.memetic.extract import build_mimetic_weather, extract_terms


def test_mwr_extract_smoke():
    docs = [
        (
            "2025-12-20T00:00:00+00:00",
            "Deepfake footage leaked. Propaganda wave rising. New term: veilbreaker.",
        ),
        (
            "2025-12-21T00:00:00+00:00",
            "Veilbreaker is trending. AI generated rumor spreads fast.",
        ),
    ]
    terms = extract_terms(docs, max_terms=20)
    assert len(terms) > 0
    units = build_mimetic_weather("r1", terms)
    assert units is not None
