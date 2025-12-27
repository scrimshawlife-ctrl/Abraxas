import argparse
import json
from pathlib import Path

from shared.evidence import load_json, sha256_file, sha256_obj
from shared.governance import record_receipt


def run(args: argparse.Namespace) -> int:
    decision = "APPROVE" if args.approve else "DENY" if args.deny else None
    if not decision:
        raise SystemExit("Must specify --approve or --deny")

    plan_obj = load_json(args.plan)
    evidence = plan_obj.get("evidence", {}) or {}

    evidence_bundle = {
        "plan_file_sha256": sha256_file(args.plan),
        "plan_sha256": evidence.get("plan_sha256") or sha256_obj(plan_obj),
        "audit_report_sha256": evidence.get("audit_report_sha256"),
        "health_state_sha256": evidence.get("health_state_sha256"),
        "policy_sha256": evidence.get("policy_sha256"),
    }

    receipt = record_receipt(
        action_rune_id=args.rune,
        action_payload={"action_plan": plan_obj.get("action_plan", [])},
        evidence_bundle=evidence_bundle,
        decision=decision,
        decided_by=args.decided_by,
        reason=args.reason,
    )

    out = Path("data") / "last_governance_receipt.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    print(receipt["governance_receipt_id"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abx govern")
    parser.add_argument("--approve", action="store_true")
    parser.add_argument("--deny", action="store_true")
    parser.add_argument(
        "--rune",
        required=True,
        help="Action rune to approve/deny, e.g. actuator.apply",
    )
    parser.add_argument(
        "--plan",
        required=True,
        help="Path to plan json (e.g. data/self_heal_plan.json)",
    )
    parser.add_argument("--decided-by", default="daniel")
    parser.add_argument("--reason", default=None)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
