from __future__ import annotations

from pathlib import Path

from abraxas.acquisition.bulk_planner import build_bulk_plan
from abraxas.acquisition.execute_plan import execute_plan
from abraxas.acquisition.manifest_schema import ManifestArtifact, ManifestProvenance
from abraxas.acquisition.plan_schema import BulkPullPlan, PlanStep
from abraxas.policy.utp import PortfolioTuningIR, UBVBudgets
from abraxas.storage.cas import CASStore


def _manifest(urls: list[str]) -> ManifestArtifact:
    provenance = ManifestProvenance(
        retrieval_method="cache_only",
        decodo_used=False,
        reason_code=None,
        raw_hash="raw",
        parse_hash="parse",
        cache_path="/tmp/cas/manifest.json",
    )
    return ManifestArtifact.build(
        source_id="TEST_SOURCE",
        retrieved_at_utc="2025-01-01T00:00:00Z",
        kind="SITEMAP",
        urls=urls,
        metadata={},
        provenance=provenance,
    )


def test_bulk_planner_respects_max_requests() -> None:
    budgets = PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=2))
    manifest = _manifest([
        "https://example.com/c",
        "https://example.com/a",
        "https://example.com/b",
    ])
    result = build_bulk_plan(
        source_id="TEST_SOURCE",
        window_utc={},
        manifest=manifest,
        budgets=budgets,
        created_at_utc="2025-01-01T00:00:00Z",
    )
    assert len(result.plan.steps) == 2
    assert [step.deterministic_order_index for step in result.plan.steps] == [0, 1]


def test_execute_plan_offline_cache_only(tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    url = "https://example.com/data.json"
    cas_store.store_bytes(b"payload", url=url, recorded_at_utc="2025-01-01T00:00:00Z")

    step = PlanStep(
        step_id="step-1",
        action="DOWNLOAD",
        url_or_key=url,
        expected_bytes=None,
        cache_policy="REQUIRED",
        codec_hint=None,
        notes=None,
        deterministic_order_index=0,
    )
    plan = BulkPullPlan.build(
        source_id="TEST_SOURCE",
        created_at_utc="2025-01-01T00:00:00Z",
        window_utc={},
        manifest_id="manifest-1",
        steps=[step],
    )

    budgets = PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=1))
    result = execute_plan(
        plan=plan,
        run_ctx={"run_id": "run-2", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=budgets,
        cas_store=cas_store,
        offline=True,
    )
    assert len(result.packets) == 1
    assert result.packets[0].provenance.get("acquisition_method") == "cache_only"
