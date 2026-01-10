"""Tests for SourceAtlas determinism and no-domain-prior handling."""

from __future__ import annotations

from abraxas.sources.atlas import build_source_atlas
from abraxas.sources.types import (
    Cadence,
    CachePolicy,
    SourceKind,
    SourceRecord,
    SourceRef,
)


def test_source_atlas_hash_stable():
    hashes = {build_source_atlas().atlas_hash() for _ in range(12)}
    assert len(hashes) == 1, "SourceAtlas hash must be stable"


def test_no_domain_prior_source_kinds():
    base = dict(
        provider="Example Provider",
        cadence=Cadence.daily,
        backfill="none",
        tvm_vectors=["V1_SIGNAL_DENSITY"],
        mda_domains=["TEST"],
        adapter="example",
        cache_policy=CachePolicy.required,
        determinism_notes="cache_required",
        provenance_notes="synthetic test record",
        refs=[SourceRef(id="test_ref", title="Test Ref", url="https://example.com")],
    )

    astro = SourceRecord(source_id="TEST_ASTROLOGY", kind=SourceKind.astrology, **base)
    meteo = SourceRecord(source_id="TEST_METEO", kind=SourceKind.meteorological_climate, **base)
    numerology = SourceRecord(source_id="TEST_NUM", kind=SourceKind.numerology, **base)
    schumann = SourceRecord(source_id="TEST_SCHUMANN", kind=SourceKind.schumann_resonance, **base)
    geomagnetic = SourceRecord(source_id="TEST_GEOMAG", kind=SourceKind.geomagnetic, **base)

    assert astro.canonical_payload().keys() == meteo.canonical_payload().keys()
    assert numerology.canonical_payload().keys() == meteo.canonical_payload().keys()
    assert schumann.canonical_payload().keys() == meteo.canonical_payload().keys()
    assert geomagnetic.canonical_payload().keys() == meteo.canonical_payload().keys()
