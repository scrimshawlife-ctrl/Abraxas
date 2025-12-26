"""
Counterfactual Replay Engine (CRE) v0.1
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml

from abraxas.backtest.component_eval import evaluate_components_for_case
from abraxas.backtest.evaluator import evaluate_case, load_backtest_case
from abraxas.backtest.portfolio import load_portfolios, select_cases_for_portfolio
from abraxas.backtest.schema import BacktestCase, BacktestResult
from abraxas.core.provenance import hash_canonical_json
from abraxas.replay.masks import apply_mask_to_influence_events
from abraxas.replay.types import ReplayInfluence, ReplayMask
from abraxas.scoreboard.aggregate import aggregate_scores_for_cases
from abraxas.scoreboard.component_ledger import ComponentScoreLedger, write_component_score_summary
from abraxas.scoreboard.components import aggregate_component_outcomes


def run_counterfactual(
    run_id: str,
    portfolio_id: str,
    masks: List[ReplayMask],
    cases_dir: str,
    portfolios_path: str,
    fdr_path: str,
    overrides_path: Optional[str] = None,
    max_cases: int = 100,
    max_ensembles: int = 50,
    emit_artifacts: bool = True,
) -> Dict[str, Any]:
    cases = _load_cases(cases_dir)
    portfolios = load_portfolios(portfolios_path)

    if portfolio_id not in portfolios:
        raise ValueError(f"Unknown portfolio_id: {portfolio_id}")

    selected_cases = select_cases_for_portfolio(cases, portfolios[portfolio_id])
    selected_cases = selected_cases[:max_cases]

    overrides = _load_overrides(overrides_path)
    influences_by_case = overrides.get("influences_by_case", {})

    baseline_results = _evaluate_cases(
        selected_cases,
        overrides.get("baseline_results"),
    )
    baseline_scores = aggregate_scores_for_cases(baseline_results)
    baseline_regime_scores = _extract_regime_scores(baseline_scores)
    baseline_forecast_scores = _extract_forecast_scores(baseline_scores)
    baseline_component_outcomes = _collect_component_outcomes(
        baseline_results, selected_cases, fdr_path
    )
    baseline_component_scores = aggregate_component_outcomes(baseline_component_outcomes)

    masked_results = _evaluate_masked_cases(
        selected_cases,
        masks,
        overrides.get("masked_results"),
        influences_by_case,
    )
    masked_scores = aggregate_scores_for_cases(masked_results)
    masked_regime_scores = _extract_regime_scores(masked_scores)
    masked_forecast_scores = _extract_forecast_scores(masked_scores)
    masked_component_outcomes = _collect_component_outcomes(
        masked_results, selected_cases, fdr_path
    )
    masked_component_scores = aggregate_component_outcomes(masked_component_outcomes)

    probability_deltas = _compute_probability_deltas(
        selected_cases,
        masks,
        influences_by_case,
        max_ensembles,
    )

    report = _build_report(
        run_id=run_id,
        portfolio_id=portfolio_id,
        masks=masks,
        baseline_scores=baseline_scores,
        masked_scores=masked_scores,
        baseline_forecast_scores=baseline_forecast_scores,
        masked_forecast_scores=masked_forecast_scores,
        baseline_regime_scores=baseline_regime_scores,
        masked_regime_scores=masked_regime_scores,
        baseline_component_scores=baseline_component_scores,
        masked_component_scores=masked_component_scores,
        probability_deltas=probability_deltas,
    )

    if emit_artifacts:
        _write_report(report)
        _append_counterfactual_ledger(report)
        _write_component_scores(run_id, masked_component_scores)

    return report


def _load_cases(cases_dir: str) -> List[BacktestCase]:
    cases_path = Path(cases_dir)
    cases: List[BacktestCase] = []
    for case_file in sorted(cases_path.glob("*.yaml")):
        with open(case_file, "r") as f:
            data = yaml.safe_load(f) or {}
        if "cases" in data:
            for case_data in data["cases"]:
                cases.append(BacktestCase(**case_data))
        else:
            cases.append(load_backtest_case(case_file))
    return sorted(cases, key=lambda c: c.case_id)


def _evaluate_cases(
    cases: Iterable[BacktestCase],
    override_results: Optional[List[BacktestResult]],
) -> List[BacktestResult]:
    if override_results is not None:
        return _coerce_results(override_results)

    return [evaluate_case(case, enable_learning=False, run_id="counterfactual") for case in cases]


def _evaluate_masked_cases(
    cases: Iterable[BacktestCase],
    masks: List[ReplayMask],
    override_results: Optional[List[BacktestResult]],
    influences_by_case: Dict[str, List[ReplayInfluence]],
) -> List[BacktestResult]:
    if override_results is not None:
        return _coerce_results(override_results)

    masked_results: List[BacktestResult] = []
    for case in cases:
        influences = influences_by_case.get(case.case_id, [])
        masked_influences = _apply_masks(influences, masks)
        case_with_mask = _attach_masked_influences(case, masked_influences)
        masked_results.append(evaluate_case(case_with_mask, enable_learning=False, run_id="counterfactual_masked"))
    return masked_results


def _apply_masks(
    influences: List[ReplayInfluence],
    masks: List[ReplayMask],
) -> List[ReplayInfluence]:
    masked = list(influences)
    for mask in masks:
        masked = apply_mask_to_influence_events(masked, mask)
    return masked


def _attach_masked_influences(
    case: BacktestCase,
    influences: List[ReplayInfluence],
) -> BacktestCase:
    case_copy = case.model_copy(deep=True)
    case_copy.forecast_delta_summary = case_copy.forecast_delta_summary or {}
    case_copy.forecast_delta_summary["masked_influences"] = [
        influence.__dict__ for influence in influences
    ]
    return case_copy


def _collect_component_outcomes(
    results: List[BacktestResult],
    cases: List[BacktestCase],
    fdr_path: str,
) -> List[Dict[str, Any]]:
    outcomes: List[Dict[str, Any]] = []
    case_map = {case.case_id: case for case in cases}
    for result in results:
        if result.component_outcomes:
            outcomes.extend(result.component_outcomes)
            continue
        case = case_map.get(result.case_id)
        if not case:
            continue
        case_outcomes = evaluate_components_for_case(
            case=case,
            events=[],
            ledgers={},
            fdr_path=fdr_path,
        )
        outcomes.extend([outcome.to_dict() for outcome in case_outcomes])
    return outcomes


def _coerce_results(results: List[Any]) -> List[BacktestResult]:
    coerced: List[BacktestResult] = []
    for result in results:
        if isinstance(result, BacktestResult):
            coerced.append(result)
        else:
            coerced.append(BacktestResult(**result))
    return coerced


def _compute_probability_deltas(
    cases: List[BacktestCase],
    masks: List[ReplayMask],
    influences_by_case: Dict[str, List[ReplayInfluence]],
    max_ensembles: int,
) -> Dict[str, Any]:
    deltas: Dict[str, Any] = {"fbe": {}, "regime": {}}
    seen = 0
    for case in cases:
        if seen >= max_ensembles:
            break
        summary = case.forecast_delta_summary or {}
        before = summary.get("probs_before", {})
        after = summary.get("probs_after", {})
        masked = summary.get("probs_after_masked", {})
        if before and after:
            if masked:
                deltas["fbe"][case.case_id] = _delta_map(after, masked)
            else:
                deltas["fbe"][case.case_id] = _delta_map(before, after)
            seen += 1

        regime = case.regime_outcome_ref or {}
        if regime:
            deltas["regime"][case.case_id] = _regime_delta(regime)
    return deltas


def _delta_map(before: Dict[str, float], after: Dict[str, float]) -> Dict[str, float]:
    return {key: after.get(key, 0.0) - before.get(key, 0.0) for key in before.keys()}


def _build_report(
    run_id: str,
    portfolio_id: str,
    masks: List[ReplayMask],
    baseline_scores: Dict[str, Any],
    masked_scores: Dict[str, Any],
    baseline_forecast_scores: Dict[str, Any],
    masked_forecast_scores: Dict[str, Any],
    baseline_regime_scores: Dict[str, Any],
    masked_regime_scores: Dict[str, Any],
    baseline_component_scores: Dict[str, Any],
    masked_component_scores: Dict[str, Any],
    probability_deltas: Dict[str, Any],
) -> Dict[str, Any]:
    mask_specs = [{"mask_id": mask.mask_id, "kind": mask.kind.value, "params": mask.params} for mask in masks]
    delta_summary = {
        "score_deltas": {
            "forecast_scores": _diff_scores(
                baseline_forecast_scores, masked_forecast_scores
            ),
            "regime_scores": _diff_scores(
                baseline_regime_scores, masked_regime_scores
            ),
            "component_scores": _diff_component_scores(
                baseline_component_scores, masked_component_scores
            ),
        },
    }

    report = {
        "run_id": run_id,
        "portfolio_id": portfolio_id,
        "masks": mask_specs,
        "baseline_scores": baseline_scores,
        "masked_scores": masked_scores,
        "baseline_forecast_scores": baseline_forecast_scores,
        "masked_forecast_scores": masked_forecast_scores,
        "baseline_regime_scores": baseline_regime_scores,
        "masked_regime_scores": masked_regime_scores,
        "baseline_component_scores": baseline_component_scores,
        "masked_component_scores": masked_component_scores,
        "probability_deltas": probability_deltas,
        "delta_summary": delta_summary,
    }
    report["counterfactual_run_id"] = _counterfactual_run_id(report)
    return report


def _diff_scores(baseline: Dict[str, Any], masked: Dict[str, Any]) -> Dict[str, Any]:
    deltas = {}
    for key, value in baseline.items():
        masked_value = masked.get(key)
        if value is None or masked_value is None:
            deltas[key] = None
        else:
            deltas[key] = masked_value - value
    return deltas


def _diff_component_scores(
    baseline: Dict[str, Any],
    masked: Dict[str, Any],
) -> Dict[str, Any]:
    deltas: Dict[str, Any] = {}
    for component_id in sorted(set(baseline.keys()) | set(masked.keys())):
        base = baseline.get(component_id, {})
        mask = masked.get(component_id, {})
        deltas[component_id] = {
            "hit_rate_delta": _safe_delta(base.get("hit_rate"), mask.get("hit_rate")),
            "brier_delta": _safe_delta(base.get("brier_avg"), mask.get("brier_avg")),
            "coverage_delta": _safe_delta(base.get("coverage_rate"), mask.get("coverage_rate")),
            "trend_acc_delta": _safe_delta(base.get("trend_acc"), mask.get("trend_acc")),
        }
    return deltas


def _safe_delta(before: Optional[float], after: Optional[float]) -> Optional[float]:
    if before is None or after is None:
        return None
    return after - before


def _counterfactual_run_id(report: Dict[str, Any]) -> str:
    mask_specs = sorted(
        [f"{mask['mask_id']}:{mask['kind']}:{mask.get('params')}" for mask in report["masks"]]
    )
    payload = {
        "run_id": report["run_id"],
        "portfolio_id": report["portfolio_id"],
        "masks": mask_specs,
    }
    return f"cfr_{hash_canonical_json(payload)[:12]}"


def _write_report(report: Dict[str, Any]) -> None:
    run_id = report["run_id"]
    portfolio_id = report["portfolio_id"]
    mask_hash = hash_canonical_json(report["masks"])[:8]
    report_id = f"{run_id}_{portfolio_id}_{mask_hash}"

    reports_dir = Path("out/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = Path("out/runs") / run_id / "replay"
    runs_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / f"counterfactual_{report_id}.json"
    md_path = reports_dir / f"counterfactual_{report_id}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    md_path.write_text(_render_report_md(report))

    run_json = runs_dir / "counterfactual_report.json"
    run_md = runs_dir / "counterfactual_report.md"
    run_json.write_text(json.dumps(report, indent=2, sort_keys=True))
    run_md.write_text(_render_report_md(report))


def _render_report_md(report: Dict[str, Any]) -> str:
    lines = [
        "# Counterfactual Replay Report",
        "",
        f"- Counterfactual Run ID: {report['counterfactual_run_id']}",
        f"- Run ID: {report['run_id']}",
        f"- Portfolio ID: {report['portfolio_id']}",
        "",
        "## Score Deltas",
    ]
    score_deltas = report["delta_summary"]["score_deltas"]
    for key, value in score_deltas.get("forecast_scores", {}).items():
        lines.append(f"- forecast.{key}: {value}")
    for key, value in score_deltas.get("regime_scores", {}).items():
        lines.append(f"- regime.{key}: {value}")

    lines.append("")
    lines.append("## Top Component Deltas")
    component_deltas = report["delta_summary"]["score_deltas"]["component_scores"]
    for component_id in sorted(component_deltas.keys()):
        lines.append(f"- {component_id}: {component_deltas[component_id]}")
    return "\n".join(lines)


def _append_counterfactual_ledger(report: Dict[str, Any]) -> None:
    ledger_path = Path("out/replay_ledgers/counterfactual_runs.jsonl")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    prev_hash = _get_last_hash(ledger_path)
    mask_params_hash = hash_canonical_json(
        {mask["mask_id"]: mask.get("params", {}) for mask in report["masks"]}
    )
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "counterfactual_run_id": report["counterfactual_run_id"],
        "run_id": report["run_id"],
        "portfolio_id": report["portfolio_id"],
        "masks": report["masks"],
        "mask_params_hash": mask_params_hash,
        "baseline_score_hash": hash_canonical_json(report["baseline_scores"]),
        "masked_score_hash": hash_canonical_json(report["masked_scores"]),
        "delta_summary_hash": hash_canonical_json(report["delta_summary"]),
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


def _load_overrides(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def run_counterfactual_exclusion(
    run_id: str,
    portfolio_id: str,
    masks: List[ReplayMask],
    cases_dir: str,
    portfolios_path: str,
    fdr_path: str,
    overrides_path: Optional[str] = None,
    max_cases: int = 100,
    max_ensembles: int = 50,
) -> Dict[str, Any]:
    return run_counterfactual(
        run_id=run_id,
        portfolio_id=portfolio_id,
        masks=masks,
        cases_dir=cases_dir,
        portfolios_path=portfolios_path,
        fdr_path=fdr_path,
        overrides_path=overrides_path,
        max_cases=max_cases,
        max_ensembles=max_ensembles,
        emit_artifacts=False,
    )


def _write_component_scores(run_id: str, scores: Dict[str, Any]) -> None:
    ledger = ComponentScoreLedger()
    for component_id in sorted(scores.keys()):
        ledger.append_score(run_id, component_id, "ALL", scores[component_id])
    write_component_score_summary(run_id, scores)


def _extract_regime_scores(scores: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "coverage_rate": scores.get("coverage_rate"),
        "trend_acc": scores.get("trend_acc"),
        "crps_avg": scores.get("crps_avg"),
    }


def _extract_forecast_scores(scores: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "brier_avg": scores.get("brier_avg"),
        "log_avg": scores.get("log_avg"),
        "calibration_error": scores.get("calibration_error"),
        "abstain_rate": scores.get("abstain_rate"),
    }


def _regime_delta(regime: Dict[str, Any]) -> Dict[str, Any]:
    baseline_p = regime.get("p_baseline", regime.get("predicted"))
    masked_p = regime.get("p_masked", regime.get("predicted_masked", baseline_p))
    return {
        "p_delta": _safe_delta(baseline_p, masked_p) or 0.0,
        "rate_delta": {
            "v_min": _safe_delta(regime.get("predicted_min"), regime.get("predicted_min_masked")) or 0.0,
            "v_max": _safe_delta(regime.get("predicted_max"), regime.get("predicted_max_masked")) or 0.0,
        },
    }
