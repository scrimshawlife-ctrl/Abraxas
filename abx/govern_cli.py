import argparse
import json
import os
from pathlib import Path

from shared.evidence import load_json, sha256_file, sha256_obj
from shared.governance import record_receipt, write_promotion_receipt


def _hash_file(path: str) -> str:
    """Compute SHA-256 hash of a file."""
    import hashlib
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run_approve(args: argparse.Namespace) -> int:
    """Approve/deny an actuator action plan (existing functionality)."""
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


def run_promote(args: argparse.Namespace) -> int:
    """Write governance receipt for rune promotion (shadow→active)."""
    rune_id = args.rune_id

    # Load registry to verify rune exists
    registry_path = Path(__file__).parent.parent / "registry" / "abx_rune_registry.json"
    if not registry_path.exists():
        print(f"ERROR: Registry not found at {registry_path}")
        return 1

    registry_data = json.loads(registry_path.read_text(encoding="utf-8"))
    rune_entry = next(
        (r for r in registry_data.get("runes", []) if r.get("rune_id") == rune_id),
        None
    )

    if not rune_entry:
        print(f"ERROR: Rune '{rune_id}' not found in registry")
        return 1

    # Compute registry snapshot hash
    registry_sha256 = _hash_file(str(registry_path))

    # Check current status
    current_status = rune_entry.get("status", "shadow")
    print(f"Rune: {rune_id}")
    print(f"Current status: {current_status}")

    # Check typed I/O requirements
    inputs = rune_entry.get("inputs", [])
    outputs = rune_entry.get("outputs", [])
    has_typed_inputs = inputs and isinstance(inputs[0], dict)
    has_typed_outputs = outputs and isinstance(outputs[0], dict)

    if not has_typed_inputs or not has_typed_outputs:
        print("WARNING: Rune does not have fully typed I/O")
        print(f"  Typed inputs: {has_typed_inputs}")
        print(f"  Typed outputs: {has_typed_outputs}")
        if not args.force:
            print("Use --force to promote anyway (not recommended)")
            return 1

    # Write promotion receipt
    receipt = write_promotion_receipt(
        rune_id=rune_id,
        registry_sha256=registry_sha256,
        decision="APPROVE",
        decided_by=args.decided_by,
        reason=args.reason,
    )

    # Save receipt to data/
    out = Path("data") / f"promotion_receipt_{rune_id.replace('.', '_')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nPromotion receipt written:")
    print(f"  Receipt ID: {receipt['governance_receipt_id']}")
    print(f"  Saved to: {out}")
    print(f"\nNext steps:")
    print(f"  1. Update registry to set status='active' for {rune_id}")
    print(f"  2. Run 'abx doctor --full' to verify promotion gates")

    return 0


def run(args: argparse.Namespace) -> int:
    """Route to appropriate subcommand handler."""
    # Legacy compatibility: if no subcommand, assume approve mode
    if not hasattr(args, 'subcommand') or args.subcommand is None:
        return run_approve(args)

    if args.subcommand == 'promote':
        return run_promote(args)

    # For explicit approve subcommand
    return run_approve(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abx govern")

    # Legacy mode: support old syntax for backwards compatibility
    # (Will be invoked when no subcommand is used)
    parser.add_argument("--approve", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--deny", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--rune", help=argparse.SUPPRESS)
    parser.add_argument("--plan", help=argparse.SUPPRESS)
    parser.add_argument("--decided-by", default="daniel", help=argparse.SUPPRESS)
    parser.add_argument("--reason", default=None, help=argparse.SUPPRESS)

    # Add subcommands
    subparsers = parser.add_subparsers(dest='subcommand', help='Governance actions')

    # Promote subcommand
    p_promote = subparsers.add_parser('promote', help='Write promotion receipt for rune')
    p_promote.add_argument('rune_id', help='Rune to promote (e.g. compression.detect)')
    p_promote.add_argument('--decided-by', default='daniel', help='Decision maker identifier')
    p_promote.add_argument('--reason', default=None, help='Human rationale for promotion')
    p_promote.add_argument('--force', action='store_true', help='Force promotion even without typed I/O')

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
