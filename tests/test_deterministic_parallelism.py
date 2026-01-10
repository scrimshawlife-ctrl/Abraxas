from __future__ import annotations

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.policy.utp import PipelineKnobs, PortfolioTuningIR, UBVBudgets
from abraxas.runtime.concurrency import ConcurrencyConfig
from abraxas.runtime.deterministic_executor import commit_results, execute_parallel, WorkResult
from abraxas.runtime.work_units import WorkUnit


def _units() -> list[WorkUnit]:
    return [
        WorkUnit.build(
            stage="FETCH",
            source_id="S1",
            window_utc={"start": "2026-01-01T00:00:00Z", "end": "2026-01-02T00:00:00Z"},
            key=("S1", "2026-01-01T00:00:00Z", "https://b"),
            input_refs={"url": "https://b"},
            input_bytes=10,
        ),
        WorkUnit.build(
            stage="FETCH",
            source_id="S1",
            window_utc={"start": "2026-01-01T00:00:00Z", "end": "2026-01-02T00:00:00Z"},
            key=("S1", "2026-01-01T00:00:00Z", "https://a"),
            input_refs={"url": "https://a"},
            input_bytes=10,
        ),
    ]


def _handler(unit: WorkUnit) -> WorkResult:
    return WorkResult(
        unit_id=unit.unit_id,
        key=unit.key,
        output_refs={"url": unit.input_refs.get("url")},
        bytes_processed=unit.input_bytes,
        stage=unit.stage,
    )


def test_parallelism_hash_invariant() -> None:
    units = _units()
    config_off = ConcurrencyConfig(enabled=False)
    config_on = ConcurrencyConfig(enabled=True, max_workers_fetch=4)

    result_off = commit_results(
        execute_parallel(units, config=config_off, stage="FETCH", handler=_handler).results
    )
    result_on = commit_results(
        execute_parallel(units, config=config_on, stage="FETCH", handler=_handler).results
    )

    hash_off = sha256_hex(canonical_json([r.output_refs for r in result_off]))
    hash_on = sha256_hex(canonical_json([r.output_refs for r in result_on]))
    assert hash_off == hash_on


def test_inflight_bytes_cap() -> None:
    units = _units()
    config_on = ConcurrencyConfig(enabled=True, max_workers_fetch=2, max_inflight_bytes=10)
    result = execute_parallel(units, config=config_on, stage="FETCH", handler=_handler)
    assert result.max_inflight_bytes <= 10


def test_budget_degradation_workers() -> None:
    portfolio = PortfolioTuningIR(
        ubv=UBVBudgets(max_requests_per_run=2),
        pipeline=PipelineKnobs(concurrency_enabled=True, max_workers_fetch=8, max_workers_parse=8),
    )
    config = ConcurrencyConfig.from_portfolio(portfolio)
    assert config.max_workers_fetch == 2
    assert config.max_workers_parse == 2
