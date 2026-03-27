from __future__ import annotations

from pathlib import Path

from abraxas.acquisition.manifest_discovery import discover_manifest
from abraxas.acquisition.reason_codes import (
    CACHE_FALLBACK_AFTER_BULK_FAILED,
    CACHE_POLICY_MANIFEST_PROBE,
    DECODO_USED,
    FETCH_FAILED,
    POLICY_CACHE_ONLY,
    UNKNOWN_POLICY_REASON,
)
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


def test_manifest_discovery_prefers_bulk_over_cache_hit(monkeypatch, tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    seed = "https://example.com/sitemap.xml"
    cas_store.store_bytes(
        b"<urlset><url><loc>https://example.com/from-cache</loc></url></urlset>",
        url=seed,
        recorded_at_utc="2025-01-01T00:00:00Z",
    )

    class _FakeRawRef:
        content_hash = "raw_hash"
        bytes = 12
        path = "/tmp/raw.bin"

    class _FakeFetch:
        body = b"<urlset><url><loc>https://example.com/from-bulk</loc></url></urlset>"
        method = "bulk"
        decodo_used = False
        raw_ref = _FakeRawRef()

    monkeypatch.setattr(
        "abraxas.acquisition.manifest_discovery.acquire_bulk",
        lambda **kwargs: _FakeFetch(),
    )

    result = discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed],
        run_ctx={"run_id": "run-1", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=5)),
        cas_store=cas_store,
        allow_decodo=False,
    )

    assert result.manifest.urls == ["https://example.com/from-bulk"]
    assert result.manifest.provenance.retrieval_method == "bulk"
    assert result.manifest.provenance.reason_code is None


def test_manifest_discovery_cache_only_mode_sets_policy_reason(tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    seed = "https://example.com/sitemap.xml"
    cas_store.store_bytes(
        b"<urlset><url><loc>https://example.com/from-cache</loc></url></urlset>",
        url=seed,
        recorded_at_utc="2025-01-01T00:00:00Z",
    )

    result = discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed],
        run_ctx={"run_id": "run-1", "now_utc": "2025-01-01T00:00:00Z", "cache_only_mode": True},
        budgets=PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=5)),
        cas_store=cas_store,
        allow_decodo=False,
    )
    assert result.manifest.provenance.retrieval_method == "cache_only"
    assert result.manifest.provenance.reason_code == POLICY_CACHE_ONLY
    seed_manifest = result.manifest.metadata.get("seed_manifests")[0]
    assert seed_manifest.get("policy_reason") == CACHE_POLICY_MANIFEST_PROBE
    assert seed_manifest.get("policy_reason_canonical") == CACHE_POLICY_MANIFEST_PROBE
    assert result.manifest.metadata.get("reason_summary") == {POLICY_CACHE_ONLY: 1}
    assert result.manifest.metadata.get("policy_summary") == {CACHE_POLICY_MANIFEST_PROBE: 1}


def test_manifest_discovery_cache_fallback_reason_is_canonical(monkeypatch, tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    seed = "https://example.com/sitemap.xml"
    cas_store.store_bytes(
        b"<urlset><url><loc>https://example.com/from-cache-fallback</loc></url></urlset>",
        url=seed,
        recorded_at_utc="2025-01-01T00:00:00Z",
    )

    def _bulk_fail(**kwargs):
        raise TimeoutError("simulated-timeout")

    monkeypatch.setattr("abraxas.acquisition.manifest_discovery.acquire_bulk", _bulk_fail)

    result = discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed],
        run_ctx={"run_id": "run-1", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=5)),
        cas_store=cas_store,
        allow_decodo=False,
    )
    assert result.manifest.provenance.retrieval_method == "cache_only"
    assert result.manifest.provenance.reason_code == CACHE_FALLBACK_AFTER_BULK_FAILED
    assert result.manifest.metadata.get("reason_summary") == {CACHE_FALLBACK_AFTER_BULK_FAILED: 1}
    assert result.manifest.metadata.get("policy_summary") == {CACHE_POLICY_MANIFEST_PROBE: 1}


def test_manifest_discovery_decodo_reason_is_canonical(monkeypatch, tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    seed = "https://example.com/sitemap.xml"

    class _FakeRawRef:
        content_hash = "raw_hash"
        bytes = 20
        path = "/tmp/raw-decodo.bin"

    class _FakeSurgicalFetch:
        body = b"<urlset><url><loc>https://example.com/from-decodo</loc></url></urlset>"
        method = "surgical"
        decodo_used = True
        raw_ref = _FakeRawRef()
        policy_reason = None

    def _bulk_fail(**kwargs):
        raise TimeoutError("simulated-timeout")

    monkeypatch.setattr("abraxas.acquisition.manifest_discovery.acquire_bulk", _bulk_fail)
    monkeypatch.setattr("abraxas.acquisition.manifest_discovery.acquire_surgical", lambda **kwargs: _FakeSurgicalFetch())

    result = discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed],
        run_ctx={"run_id": "run-1", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=5)),
        cas_store=cas_store,
        allow_decodo=True,
    )

    assert result.manifest.provenance.retrieval_method == "surgical"
    assert result.manifest.provenance.reason_code == DECODO_USED
    assert result.manifest.metadata.get("reason_summary") == {DECODO_USED: 1}
    assert result.manifest.metadata.get("policy_summary") == {}


def test_manifest_discovery_unclassified_fetch_failure_uses_fetch_failed_bucket(monkeypatch, tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    seed = "https://example.com/sitemap.xml"

    monkeypatch.setattr(
        "abraxas.acquisition.manifest_discovery._fetch_seed",
        lambda *args, **kwargs: (None, None),
    )

    result = discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed],
        run_ctx={"run_id": "run-1", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=5)),
        cas_store=cas_store,
        allow_decodo=False,
    )

    assert result.manifest.provenance.reason_code == FETCH_FAILED
    assert result.manifest.metadata.get("reason_summary") == {FETCH_FAILED: 1}
    assert result.manifest.metadata.get("policy_summary") == {}


def test_manifest_discovery_unknown_policy_reason_is_bucketed(monkeypatch, tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    seed = "https://example.com/sitemap.xml"
    cas_store.store_bytes(
        b"<urlset><url><loc>https://example.com/from-bulk</loc></url></urlset>",
        url=seed,
        recorded_at_utc="2025-01-01T00:00:00Z",
    )

    class _FakeRawRef:
        content_hash = "raw_hash"
        bytes = 12
        path = "/tmp/raw.bin"

    class _FakeFetch:
        body = b"<urlset><url><loc>https://example.com/from-bulk</loc></url></urlset>"
        method = "bulk"
        decodo_used = False
        raw_ref = _FakeRawRef()
        policy_reason = "custom_policy"

    monkeypatch.setattr(
        "abraxas.acquisition.manifest_discovery.acquire_bulk",
        lambda **kwargs: _FakeFetch(),
    )

    result = discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed],
        run_ctx={"run_id": "run-1", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=5)),
        cas_store=cas_store,
        allow_decodo=False,
    )

    seed_manifest = result.manifest.metadata.get("seed_manifests")[0]
    assert seed_manifest.get("policy_reason") == "custom_policy"
    assert seed_manifest.get("policy_reason_canonical") == UNKNOWN_POLICY_REASON
    assert result.manifest.metadata.get("policy_summary") == {UNKNOWN_POLICY_REASON: 1}
