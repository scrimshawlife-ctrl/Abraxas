"""
Counterfactual CLI
"""

from __future__ import annotations

from typing import List

from abraxas.replay.counterfactual import run_counterfactual
from abraxas.replay.types import ReplayMask, ReplayMaskKind


def run_counterfactual_cli(args) -> int:
    masks = [parse_mask_spec(spec) for spec in args.mask]

    report = run_counterfactual(
        run_id=args.run_id,
        portfolio_id=args.portfolio,
        masks=masks,
        cases_dir=args.cases_dir,
        portfolios_path=args.portfolios_path,
        fdr_path=args.fdr_path,
        overrides_path=args.overrides_path,
    )

    print("Counterfactual Run:", report["counterfactual_run_id"])
    score_deltas = report["delta_summary"]["score_deltas"]
    print("Score Deltas:", score_deltas)
    _print_top_probability_shifts(report)
    _print_top_component_deltas(score_deltas.get("component_scores", {}))
    return 0


def parse_mask_spec(spec: str) -> ReplayMask:
    if spec == "exclude_quarantined":
        return ReplayMask(
            mask_id="exclude_quarantined",
            kind=ReplayMaskKind.EXCLUDE_QUARANTINED,
            params={},
            description="Exclude quarantined influences",
        )

    if spec == "only_evidence_pack":
        return ReplayMask(
            mask_id="only_evidence_pack",
            kind=ReplayMaskKind.ONLY_EVIDENCE_PACK,
            params={},
            description="Keep only evidence pack influences",
        )

    if spec.startswith("exclude_sources="):
        labels = spec.split("=", 1)[1].split(",")
        return ReplayMask(
            mask_id="exclude_sources",
            kind=ReplayMaskKind.EXCLUDE_SOURCE_LABELS,
            params={"source_labels": labels},
            description="Exclude source labels",
        )

    if spec.startswith("clamp_siw_max="):
        max_w = float(spec.split("=", 1)[1])
        return ReplayMask(
            mask_id="clamp_siw_max",
            kind=ReplayMaskKind.CLAMP_SIW_MAX,
            params={"max_w": max_w},
            description="Clamp SIW max",
        )

    if spec.startswith("exclude_domain="):
        domain = spec.split("=", 1)[1]
        return ReplayMask(
            mask_id="exclude_domain",
            kind=ReplayMaskKind.EXCLUDE_DOMAIN,
            params={"domain": domain},
            description="Exclude domain",
        )

    raise ValueError(f"Unknown mask spec: {spec}")


def _print_top_probability_shifts(report) -> None:
    deltas = report.get("probability_deltas", {}).get("fbe", {})
    shifts = []
    for case_id, delta_map in deltas.items():
        for branch_id, delta in delta_map.items():
            shifts.append((abs(delta), case_id, branch_id, delta))
    shifts.sort(reverse=True)
    print("Top Probability Shifts:")
    for _, case_id, branch_id, delta in shifts[:10]:
        print(f"- {case_id}:{branch_id} {delta:+.4f}")


def _print_top_component_deltas(component_deltas) -> None:
    ranked = []
    for component_id, delta in component_deltas.items():
        score = abs(delta.get("brier_delta") or 0.0) + abs(delta.get("hit_rate_delta") or 0.0)
        ranked.append((score, component_id, delta))
    ranked.sort(reverse=True)
    print("Top Component Sensitivity:")
    for _, component_id, delta in ranked[:10]:
        print(f"- {component_id}: {delta}")
