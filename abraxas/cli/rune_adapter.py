"""Rune adapter for CLI capabilities."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.cli.counterfactual import parse_mask_spec
from abraxas.core.provenance import canonical_envelope
from abraxas.replay.counterfactual import run_counterfactual
from abraxas.value.smv import build_units_from_vector_map, run_smv


def _format_counterfactual_output(report: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    lines.append(f"Counterfactual Run: {report.get('counterfactual_run_id')}")
    score_deltas = report.get("delta_summary", {}).get("score_deltas", {})
    lines.append(f"Score Deltas: {score_deltas}")

    deltas = report.get("probability_deltas", {}).get("fbe", {})
    shifts = []
    for case_id, delta_map in deltas.items():
        for branch_id, delta in delta_map.items():
            shifts.append((abs(delta), case_id, branch_id, delta))
    shifts.sort(reverse=True)
    lines.append("Top Probability Shifts:")
    for _, case_id, branch_id, delta in shifts[:10]:
        lines.append(f"- {case_id}:{branch_id} {delta:+.4f}")

    component_deltas = score_deltas.get("component_scores", {})
    ranked = []
    for component_id, delta in component_deltas.items():
        score = abs(delta.get("brier_delta") or 0.0) + abs(delta.get("hit_rate_delta") or 0.0)
        ranked.append((score, component_id, delta))
    ranked.sort(reverse=True)
    lines.append("Top Component Sensitivity:")
    for _, component_id, delta in ranked[:10]:
        lines.append(f"- {component_id}: {delta}")

    return lines


def _format_smv_output(report: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    lines.append(f"Baseline Scores: {report.get('baseline_scores')}")
    lines.append("Top Units:")
    for unit in report.get("units", [])[:10]:
        lines.append(f"- {unit['unit_id']} ({unit['kind']}): {unit['smv_overall']:.4f}")
    lines.append("Bottom Units:")
    for unit in report.get("units", [])[-10:]:
        lines.append(f"- {unit['unit_id']} ({unit['kind']}): {unit['smv_overall']:.4f}")
    lines.append("Positive SMV means this unit helps accuracy/robustness.")
    return lines


def run_counterfactual_cli_deterministic(
    portfolio: str,
    mask: List[str],
    run_id: str,
    cases_dir: str,
    portfolios_path: str,
    fdr_path: str,
    overrides_path: Optional[str] = None,
    seed: Optional[int] = None,
    strict_execution: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    _ = strict_execution
    masks = [parse_mask_spec(spec) for spec in mask]
    report = run_counterfactual(
        run_id=run_id,
        portfolio_id=portfolio,
        masks=masks,
        cases_dir=cases_dir,
        portfolios_path=portfolios_path,
        fdr_path=fdr_path,
        overrides_path=overrides_path,
    )
    output_lines = _format_counterfactual_output(report)

    envelope = canonical_envelope(
        result={"report": report, "output_lines": output_lines},
        config={},
        inputs={
            "portfolio": portfolio,
            "mask": mask,
            "run_id": run_id,
            "cases_dir": cases_dir,
            "portfolios_path": portfolios_path,
            "fdr_path": fdr_path,
            "overrides_path": overrides_path,
        },
        operation_id="replay.counterfactual.run_cli",
        seed=seed,
    )

    return {
        "exit_code": 0,
        "report": report,
        "output_lines": output_lines,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }


def run_smv_cli_deterministic(
    portfolio: str,
    vector_map: str,
    allowlist_spec: Optional[str],
    run_id: str,
    cases_dir: str,
    portfolios_path: str,
    max_units: int,
    seed: Optional[int] = None,
    strict_execution: bool = True,
    **kwargs: Any,
) -> Dict[str, Any]:
    _ = strict_execution
    units = build_units_from_vector_map(vector_map, allowlist_spec)
    report = run_smv(
        run_id=run_id,
        portfolio_id=portfolio,
        units=units,
        cases_dir=cases_dir,
        portfolios_path=portfolios_path,
        vector_map_path=vector_map,
        max_units=max_units,
    )
    output_lines = _format_smv_output(report)

    envelope = canonical_envelope(
        result={"report": report, "output_lines": output_lines},
        config={},
        inputs={
            "portfolio": portfolio,
            "vector_map": vector_map,
            "allowlist_spec": allowlist_spec,
            "run_id": run_id,
            "cases_dir": cases_dir,
            "portfolios_path": portfolios_path,
            "max_units": max_units,
        },
        operation_id="value.smv.run_cli",
        seed=seed,
    )

    return {
        "exit_code": 0,
        "report": report,
        "output_lines": output_lines,
        "provenance": envelope["provenance"],
        "not_computable": envelope["not_computable"],
    }
