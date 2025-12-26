"""
Signal Marginal Value (SMV) v0.1
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from abraxas.core.provenance import hash_canonical_json
from abraxas.online.vector_map_loader import load_vector_map
from abraxas.replay.counterfactual import run_counterfactual_exclusion
from abraxas.replay.types import ReplayMask, ReplayMaskKind
from abraxas.value.types import SMVUnit, SMVUnitKind


def build_units_from_vector_map(
    vector_map_path: str,
    allowlist_spec_path: Optional[str] = None,
) -> List[SMVUnit]:
    vector_map = load_vector_map(Path(vector_map_path))
    units: List[SMVUnit] = []
    for node in vector_map.nodes:
        units.append(
            SMVUnit(
                unit_id=node.node_id,
                kind=SMVUnitKind.VECTOR_NODE,
                selectors={"node_id": node.node_id},
                description=node.description,
            )
        )
        for source_id in node.allowlist_source_ids:
            units.append(
                SMVUnit(
                    unit_id=source_id,
                    kind=SMVUnitKind.SOURCE_LABEL,
                    selectors={"source_labels": [source_id]},
                    description=f"Source label {source_id}",
                )
            )

    units = _dedupe_units(units)
    return sorted(units, key=lambda u: (u.kind.value, u.unit_id))


def build_units_from_recent_ledgers(
    run_id: str,
    max_units: int = 50,
) -> List[SMVUnit]:
    return []


def run_smv(
    run_id: str,
    portfolio_id: str,
    units: List[SMVUnit],
    cases_dir: str,
    portfolios_path: str,
    vector_map_path: Optional[str],
    max_units: int = 25,
    overrides_path: Optional[str] = None,
) -> Dict[str, Any]:
    overrides = _load_overrides(overrides_path)
    baseline_report = run_counterfactual_exclusion(
        run_id=run_id,
        portfolio_id=portfolio_id,
        masks=[],
        cases_dir=cases_dir,
        portfolios_path=portfolios_path,
        fdr_path=overrides.get("fdr_path", "data/forecast/decomposition/fdr_v0_1.yaml"),
        overrides_path=overrides_path,
    )

    baseline_scores = baseline_report["baseline_scores"]
    baseline_forecast = baseline_report["baseline_forecast_scores"]
    baseline_regime = baseline_report["baseline_regime_scores"]

    results = []
    for unit in units[:max_units]:
        mask = _unit_to_mask(unit, vector_map_path)
        if mask is None:
            continue
        unit_overrides = _unit_overrides(overrides, unit.unit_id)
        report = run_counterfactual_exclusion(
            run_id=run_id,
            portfolio_id=portfolio_id,
            masks=[mask],
            cases_dir=cases_dir,
            portfolios_path=portfolios_path,
            fdr_path=overrides.get("fdr_path", "data/forecast/decomposition/fdr_v0_1.yaml"),
            overrides_path=unit_overrides,
        )

        masked_scores = report["masked_scores"]
        masked_forecast = report["masked_forecast_scores"]
        masked_regime = report["masked_regime_scores"]
        benefit = _compute_benefit(
            baseline_forecast,
            baseline_regime,
            masked_forecast,
            masked_regime,
        )
        cost = _unit_cost(overrides, unit.unit_id)
        risk = _unit_risk(overrides, unit.unit_id)
        smv_overall, smv_by_metric = _compute_smv(benefit, cost, risk)

        results.append(
            {
                "unit_id": unit.unit_id,
                "kind": unit.kind.value,
                "benefit": benefit,
                "cost": cost,
                "risk": risk,
                "smv_overall": smv_overall,
                "smv_by_metric": smv_by_metric,
                "notes": [],
            }
        )

    results.sort(key=lambda r: r["smv_overall"], reverse=True)
    report = {
        "run_id": run_id,
        "portfolio_id": portfolio_id,
        "baseline_scores": baseline_scores,
        "units": results,
    }
    report["smv_run_id"] = _smv_run_id(report)
    _write_report(report)
    _append_smv_ledger(report)
    return report


def _unit_to_mask(unit: SMVUnit, vector_map_path: Optional[str]) -> Optional[ReplayMask]:
    if unit.kind == SMVUnitKind.SOURCE_LABEL:
        return ReplayMask(
            mask_id=f"exclude_source_{unit.unit_id}",
            kind=ReplayMaskKind.EXCLUDE_SOURCE_LABELS,
            params={"source_labels": unit.selectors.get("source_labels", [])},
            description="Exclude source label",
        )
    if unit.kind == SMVUnitKind.VECTOR_NODE:
        source_labels = []
        if vector_map_path:
            vector_map = load_vector_map(Path(vector_map_path))
            for node in vector_map.nodes:
                if node.node_id == unit.selectors.get("node_id"):
                    source_labels = node.allowlist_source_ids
                    break
        return ReplayMask(
            mask_id=f"exclude_node_{unit.unit_id}",
            kind=ReplayMaskKind.EXCLUDE_SOURCE_LABELS,
            params={"source_labels": source_labels},
            description="Exclude vector node sources",
        )
    if unit.kind == SMVUnitKind.DOMAIN:
        return ReplayMask(
            mask_id=f"exclude_domain_{unit.unit_id}",
            kind=ReplayMaskKind.EXCLUDE_DOMAIN,
            params={"domain": unit.selectors.get("domain")},
            description="Exclude domain",
        )
    if unit.kind == SMVUnitKind.CLASS:
        kind = unit.selectors.get("class")
        if kind == "quarantined_online":
            return ReplayMask(
                mask_id=f"exclude_class_{unit.unit_id}",
                kind=ReplayMaskKind.EXCLUDE_QUARANTINED,
                params={},
                description="Exclude quarantined",
            )
        if kind == "evidence_pack":
            return ReplayMask(
                mask_id=f"only_class_{unit.unit_id}",
                kind=ReplayMaskKind.ONLY_EVIDENCE_PACK,
                params={},
                description="Only evidence_pack",
            )
    return None


def _compute_benefit(
    baseline_forecast: Dict[str, Any],
    baseline_regime: Dict[str, Any],
    masked_forecast: Dict[str, Any],
    masked_regime: Dict[str, Any],
) -> Dict[str, float]:
    benefit = {}
    for key, value in baseline_forecast.items():
        masked_value = masked_forecast.get(key)
        benefit[key] = _benefit_value(key, value, masked_value)
    for key, value in baseline_regime.items():
        masked_value = masked_regime.get(key)
        benefit[key] = _benefit_value(key, value, masked_value)
    return benefit


def _benefit_value(metric: str, baseline: Optional[float], masked: Optional[float]) -> float:
    if baseline is None or masked is None:
        return 0.0
    delta = masked - baseline
    if metric in ("brier_avg", "log_avg", "crps_avg", "calibration_error"):
        return -delta
    return delta


def _compute_smv(
    benefit: Dict[str, float],
    cost: Dict[str, float],
    risk: Dict[str, float],
) -> tuple[float, Dict[str, float]]:
    cost_norm = cost.get("event_count", 0.0)
    risk_norm = risk.get("quarantined_ratio", 0.0) * risk.get("ssi_mean", 0.0)
    denom = 1.0 + cost_norm + risk_norm

    smv_by_metric = {metric: value / denom for metric, value in benefit.items()}
    smv_overall = sum(smv_by_metric.values()) / len(smv_by_metric) if smv_by_metric else 0.0
    return smv_overall, smv_by_metric


def _unit_cost(overrides: Dict[str, Any], unit_id: str) -> Dict[str, float]:
    return overrides.get("unit_costs", {}).get(unit_id, {"event_count": 0.0, "cpu_ms": 0.0})


def _unit_risk(overrides: Dict[str, Any], unit_id: str) -> Dict[str, float]:
    return overrides.get("unit_risks", {}).get(unit_id, {"quarantined_ratio": 0.0, "ssi_mean": 0.0})


def _load_overrides(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def _unit_overrides(overrides: Dict[str, Any], unit_id: str) -> Optional[str]:
    return overrides.get("masked_overrides_by_unit", {}).get(unit_id)


def _write_report(report: Dict[str, Any]) -> None:
    reports_dir = Path("out/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_id = f"{report['run_id']}_{report['portfolio_id']}"
    json_path = reports_dir / f"smv_{report_id}.json"
    md_path = reports_dir / f"smv_{report_id}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    md_path.write_text(_render_report_md(report))


def _render_report_md(report: Dict[str, Any]) -> str:
    lines = [
        "# Signal Marginal Value Report",
        "",
        f"- SMV Run ID: {report['smv_run_id']}",
        f"- Run ID: {report['run_id']}",
        f"- Portfolio ID: {report['portfolio_id']}",
        "",
        "## Top Units",
    ]
    for unit in report["units"][:10]:
        lines.append(f"- {unit['unit_id']}: {unit['smv_overall']:.4f}")
    return "\n".join(lines)


def _append_smv_ledger(report: Dict[str, Any]) -> None:
    ledger_path = Path("out/value_ledgers/smv_runs.jsonl")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash = _get_last_hash(ledger_path)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "smv_run_id": report["smv_run_id"],
        "run_id": report["run_id"],
        "portfolio_id": report["portfolio_id"],
        "top_units_hash": hash_canonical_json(report["units"][:10]),
        "baseline_score_hash": hash_canonical_json(report["baseline_scores"]),
        "prev_hash": prev_hash,
    }
    step_hash = hash_canonical_json(entry)
    entry["step_hash"] = step_hash
    with open(ledger_path, "a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")


def _get_last_hash(path: Path) -> str:
    if not path.exists():
        return "genesis"
    lines = path.read_text().splitlines()
    if not lines:
        return "genesis"
    last = json.loads(lines[-1])
    return last.get("step_hash", "genesis")


def _smv_run_id(report: Dict[str, Any]) -> str:
    payload = {
        "run_id": report["run_id"],
        "portfolio_id": report["portfolio_id"],
        "units": [unit["unit_id"] for unit in report["units"]],
    }
    return f"smv_{hash_canonical_json(payload)[:12]}"


def _dedupe_units(units: List[SMVUnit]) -> List[SMVUnit]:
    seen = set()
    deduped = []
    for unit in units:
        key = (unit.kind.value, unit.unit_id)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(unit)
    return deduped
