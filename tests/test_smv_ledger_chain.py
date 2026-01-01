"""
Tests for SMV ledger chaining.
"""

from pathlib import Path

import yaml

from abraxas.backtest.schema import BacktestResult, BacktestStatus, Confidence
from abraxas.value.smv import build_units_from_vector_map, run_smv


def test_smv_ledger_chain(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    vector_map_path = tmp_path / "vector_map.yaml"
    vector_map_path.write_text(
        """
version: "0.1.0"
created_at: "2025-12-26"
nodes:
  - node_id: "node_a"
    domain: "INTEGRITY"
    description: "Node A"
    allowlist_source_ids: ["src_a"]
    cadence_hint: "daily"
    narrative_affinity: ["N1_primary"]
    enabled: true
settings:
  max_nodes_active: 10
  min_allowlist_sources_per_node: 1
  max_allowlist_sources_per_node: 5
  require_domain_validation: true
  allowed_domains: ["INTEGRITY", "PROPAGANDA", "AALMANAC", "MW"]
  allowed_cadences: ["hourly", "daily", "weekly"]
""".lstrip()
    )

    portfolios_path = tmp_path / "portfolios.yaml"
    portfolios_path.write_text(
        yaml.safe_dump(
            {
                "portfolios": [
                    {
                        "portfolio_id": "smv_portfolio",
                        "horizons": [],
                        "segments": [],
                        "narratives": [],
                        "case_selectors": [],
                        "protected": False,
                    }
                ]
            },
            sort_keys=False,
        )
    )

    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()

    baseline_result = BacktestResult(
        case_id="case_smv",
        status=BacktestStatus.HIT,
        score=1.0,
        confidence=Confidence.HIGH,
        forecast_scoring={"brier": 0.2},
    )
    overrides_path = tmp_path / "overrides.yaml"
    overrides_path.write_text(
        yaml.safe_dump({"baseline_results": [baseline_result.model_dump()]}, sort_keys=False)
    )

    units = build_units_from_vector_map(str(vector_map_path))

    run_smv(
        run_id="smv_run_1",
        portfolio_id="smv_portfolio",
        units=units,
        cases_dir=str(cases_dir),
        portfolios_path=str(portfolios_path),
        vector_map_path=str(vector_map_path),
        max_units=1,
        overrides_path=str(overrides_path),
    )
    run_smv(
        run_id="smv_run_2",
        portfolio_id="smv_portfolio",
        units=units,
        cases_dir=str(cases_dir),
        portfolios_path=str(portfolios_path),
        vector_map_path=str(vector_map_path),
        max_units=1,
        overrides_path=str(overrides_path),
    )

    ledger_path = Path("out/value_ledgers/smv_runs.jsonl")
    lines = ledger_path.read_text().strip().splitlines()
    assert len(lines) == 2
    first = yaml.safe_load(lines[0])
    second = yaml.safe_load(lines[1])
    assert second["prev_hash"] == first["step_hash"]
