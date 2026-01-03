from __future__ import annotations

from pathlib import Path

from abraxas.acquisition.execute_plan import execute_plan
from abraxas.acquisition.manifest_discovery import discover_manifest
from abraxas.acquisition.perf_ledger import PerfLedger
from abraxas.acquisition.plan_schema import BulkPullPlan, PlanStep
from abraxas.policy.utp import PortfolioTuningIR, UBVBudgets
from abraxas.storage.cas import CASStore


def test_perf_ledger_emits_events(tmp_path: Path) -> None:
    cas_store = CASStore(base_dir=tmp_path / "cas")
    perf_ledger = PerfLedger(path=tmp_path / "perf.jsonl")
    seed_url = "https://example.com/sitemap.xml"
    cas_store.store_bytes(
        b"<urlset><url><loc>https://example.com/a</loc></url></urlset>",
        url=seed_url,
        recorded_at_utc="2025-01-01T00:00:00Z",
    )

    budgets = PortfolioTuningIR(ubv=UBVBudgets(max_requests_per_run=1))
    discover_manifest(
        source_id="TEST_SOURCE",
        seed_targets=[seed_url],
        run_ctx={"run_id": "run-3", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=budgets,
        cas_store=cas_store,
        perf_ledger=perf_ledger,
        allow_decodo=False,
    )

    step = PlanStep(
        step_id="step-1",
        action="DOWNLOAD",
        url_or_key=seed_url,
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

    execute_plan(
        plan=plan,
        run_ctx={"run_id": "run-4", "now_utc": "2025-01-01T00:00:00Z"},
        budgets=budgets,
        cas_store=cas_store,
        perf_ledger=perf_ledger,
        offline=True,
    )

    lines = perf_ledger.path.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 2
