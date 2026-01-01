"""
SMV CLI
"""

from __future__ import annotations

from abraxas.value.smv import build_units_from_vector_map, run_smv


def run_smv_cli(args) -> int:
    units = build_units_from_vector_map(args.vector_map, args.allowlist_spec)
    report = run_smv(
        run_id=args.run_id,
        portfolio_id=args.portfolio,
        units=units,
        cases_dir=args.cases_dir,
        portfolios_path=args.portfolios_path,
        vector_map_path=args.vector_map,
        max_units=args.max_units,
    )

    print("Baseline Scores:", report["baseline_scores"])
    print("Top Units:")
    for unit in report["units"][:10]:
        print(f"- {unit['unit_id']} ({unit['kind']}): {unit['smv_overall']:.4f}")
    print("Bottom Units:")
    for unit in report["units"][-10:]:
        print(f"- {unit['unit_id']} ({unit['kind']}): {unit['smv_overall']:.4f}")
    print("Positive SMV means this unit helps accuracy/robustness.")
    return 0
