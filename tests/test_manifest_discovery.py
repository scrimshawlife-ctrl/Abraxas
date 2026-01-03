from __future__ import annotations

from pathlib import Path

from abraxas.acquisition.manifest_discovery import discover_manifest
from abraxas.policy.utp import PortfolioTuningIR, UBVBudgets
from abraxas.storage.cas import CASStore


def test_manifest_discovery_stable_ordering(tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    seed_a = "https://example.com/sitemap.xml"
    seed_b = "https://example.com/index.html"

    cas_store.store_bytes(
        b"<urlset><url><loc>https://example.com/b</loc></url></urlset>",
        url=seed_a,
        recorded_at_utc="2025-01-01T00:00:00Z",
    )
    cas_store.store_bytes(
        b"<html><a href='https://example.com/a'></a></html>",
        url=seed_b,
        recorded_at_utc="2025-01-01T00:00:00Z",
    )

    result = discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed_b, seed_a],
        run_ctx={"run_id": "run-1", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=5)),
        cas_store=cas_store,
        allow_decodo=False,
    )

    manifest = result.manifest
    assert manifest.urls == ["https://example.com/a", "https://example.com/b"]
    seed_entries = manifest.metadata.get("seed_manifests")
    assert [entry["seed_url"] for entry in seed_entries] == sorted([seed_a, seed_b])
