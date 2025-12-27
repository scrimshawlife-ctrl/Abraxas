import argparse
import json
from pathlib import Path
import subprocess

from abx.kernel import invoke
from infra.health_probes import basic_health_state
from shared.evidence import sha256_file
from shared.policy import load_policy


def run(args: argparse.Namespace) -> int:
    if not args.plan:
        raise SystemExit("Only advisory mode supported here. Use --plan.")

    audit_path = Path(args.audit)
    if not audit_path.exists():
        subprocess.check_call(["python3", "tools/audit_repo.py"])
        audit_path = Path("data/audit_report.json")

    audit_sha = sha256_file(str(audit_path))

    policy_doc = load_policy()
    services = policy_doc.get("services", {}) or {}
    daemon_service = services.get("daemon_service", "abraxas-daemon")
    disk_path = services.get("disk_path", "/")
    health_state = basic_health_state(
        daemon_service=daemon_service, disk_path=disk_path
    )
    policy = {
        "min_disk_free_pct": 5,
        "daemon_service": daemon_service,
        "disk_path": disk_path,
    }

    response = invoke(
        rune_id="infra.self_heal",
        payload={
            "health_state": health_state,
            "policy": policy,
            "audit_report_sha256": audit_sha,
        },
        context={},
    )

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(
        json.dumps(response["result"], indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(str(outp))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="abx self-heal")
    parser.add_argument(
        "--plan", action="store_true", help="Generate advisory plan only"
    )
    parser.add_argument(
        "--out", default="data/self_heal_plan.json", help="Plan output path"
    )
    parser.add_argument(
        "--audit",
        default="data/audit_report.json",
        help="Use this audit report as evidence",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(run(args))


if __name__ == "__main__":
    main()
