from __future__ import annotations

import argparse
import json
from pathlib import Path

from abraxas_ase.export_pack import build_export_pack
from abraxas_ase.leakage_linter import lint_report_for_tier
from abraxas_ase.provenance import stable_json_dumps


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m abraxas_ase.tools.export_pack")
    ap.add_argument("--report", required=True, help="Path to daily_report.json")
    ap.add_argument("--outdir", required=True, help="Output directory for export packs")
    ap.add_argument("--tier", required=True, choices=["psychonaut", "academic", "enterprise"])
    ap.add_argument("--safe-export", action="store_true", default=False)
    ap.add_argument("--include-urls", action="store_true", default=False)
    args = ap.parse_args()

    report_path = Path(args.report)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    tier_norm = args.tier.lower()
    safe_export = args.safe_export
    if tier_norm in {"psychonaut", "academic"}:
        safe_export = True
    if tier_norm != "enterprise" and args.include_urls:
        raise SystemExit("--include-urls is only valid for enterprise tier")

    violations = lint_report_for_tier(report, tier=tier_norm)
    if violations:
        msg = "\n".join(violations)
        raise SystemExit(f"Export pack blocked due to tier leakage:\n{msg}")

    summary = build_export_pack(
        outdir=Path(args.outdir),
        report=report,
        tier=tier_norm,
        safe_export=safe_export,
        include_urls=args.include_urls,
    )
    print(stable_json_dumps({"status": "ok", **summary}))


if __name__ == "__main__":
    main()
