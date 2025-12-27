from __future__ import annotations

import argparse
import json
import os
import subprocess
from typing import Dict

from abraxas.artifacts.proof_bundle import generate_proof_bundle


def main() -> int:
    p = argparse.ArgumentParser(description="Emit non-truncated proof bundle")
    p.add_argument("--run-id", required=True)
    p.add_argument("--out-reports", default="out/reports")
    p.add_argument("--bundle-root", default="out/proof_bundles")
    p.add_argument("--include-dossiers", action="store_true")
    p.add_argument("--include-receipts", action="store_true")
    p.add_argument("--include-dossier-index", action="store_true")
    args = p.parse_args()

    run_id = args.run_id
    out_reports = args.out_reports

    subprocess.check_call(["python", "-m", "abx.due_outcomes", "--run-id", run_id])
    subprocess.check_call(
        [
            "python",
            "-m",
            "abx.scoreboard",
            "--run-id",
            run_id,
            "--out-reports",
            out_reports,
        ]
    )

    if args.include_dossiers:
        a2_path = os.path.join(out_reports, f"a2_phase_{run_id}.json")
        try:
            with open(a2_path, "r", encoding="utf-8") as f:
                a2 = json.load(f)
            profiles = (a2.get("views") or {}).get("profiles_top") or []
            terms = []
            for profile in profiles[:10]:
                if isinstance(profile, dict) and profile.get("term"):
                    terms.append(str(profile.get("term")))
            for term in terms:
                subprocess.check_call(
                    [
                        "python",
                        "-m",
                        "abx.term_dossier",
                        "--run-id",
                        run_id,
                        "--term",
                        term,
                        "--out-reports",
                        out_reports,
                    ]
                )
        except Exception:
            pass

    if args.include_receipts:
        due_path = os.path.join(out_reports, f"due_outcomes_{run_id}.json")
        try:
            with open(due_path, "r", encoding="utf-8") as f:
                due = json.load(f)
            rows = due.get("due") or []
            for row in rows[:20]:
                pred_id = row.get("pred_id")
                if pred_id:
                    subprocess.check_call(
                        [
                            "python",
                            "-m",
                            "abx.prediction_receipt",
                            "--pred-id",
                            str(pred_id),
                            "--run-id",
                            run_id,
                            "--out-reports",
                            out_reports,
                        ]
                    )
        except Exception:
            pass

    if args.include_dossier_index or args.include_dossiers or args.include_receipts:
        subprocess.check_call(
            [
                "python",
                "-m",
                "abx.dossier_index",
                "--run-id",
                run_id,
                "--out-reports",
                out_reports,
            ]
        )

    artifacts: Dict[str, str] = {
        "mwr_json": os.path.join(out_reports, f"mwr_{run_id}.json"),
        "mwr_md": os.path.join(out_reports, f"mwr_{run_id}.md"),
        "a2_phase_json": os.path.join(out_reports, f"a2_phase_{run_id}.json"),
        "a2_phase_md": os.path.join(out_reports, f"a2_phase_{run_id}.md"),
        "a2_missed_json": os.path.join(out_reports, f"a2_missed_{run_id}.json"),
        "a2_missed_md": os.path.join(out_reports, f"a2_missed_{run_id}.md"),
        "forecast_score_json": os.path.join(out_reports, f"forecast_score_{run_id}.json"),
        "forecast_score_md": os.path.join(out_reports, f"forecast_score_{run_id}.md"),
        "epp_json": os.path.join(out_reports, f"epp_{run_id}.json"),
        "epp_md": os.path.join(out_reports, f"epp_{run_id}.md"),
        "due_outcomes_json": os.path.join(out_reports, f"due_outcomes_{run_id}.json"),
        "scoreboard_md": os.path.join(out_reports, f"scoreboard_{run_id}.md"),
    }
    dossier_index_path = os.path.join(out_reports, f"dossier_index_{run_id}.json")
    if os.path.exists(dossier_index_path):
        artifacts["dossier_index_json"] = dossier_index_path

    ledger_pointer = {
        "predictions": "out/forecast_ledger/predictions.jsonl",
        "outcomes": "out/forecast_ledger/outcomes.jsonl",
        "audits": "out/forecast_ledger/audits.jsonl",
        "epp_runs": "out/value_ledgers/epp_runs.jsonl",
        "mwr_runs": "out/value_ledgers/mwr_runs.jsonl",
    }

    result = generate_proof_bundle(
        run_id=run_id,
        artifacts=artifacts,
        bundle_root=args.bundle_root,
        ledger_pointer=ledger_pointer,
    )
    print("[PROOF_BUNDLE] wrote:", result["bundle_dir"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
