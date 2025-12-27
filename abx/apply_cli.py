import argparse
import json
from pathlib import Path

from abx.kernel import invoke
from shared.evidence import load_json


def run(args: argparse.Namespace) -> int:
    plan_obj = load_json(args.plan)
    action_plan = plan_obj.get("action_plan", []) or []

    response = invoke(
        rune_id="actuator.apply",
        payload={
            "action_plan": action_plan,
            "governance_receipt_id": args.receipt,
            "dry_run": bool(args.dry_run),
        },
        context={},
    )

    outp = Path("data") / "last_apply_result.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(
        json.dumps(response, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(str(outp))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abx apply")
    parser.add_argument("--receipt", required=True, help="governance_receipt_id")
    parser.add_argument("--plan", required=True, help="Path to plan json")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate apply without executing actions",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
