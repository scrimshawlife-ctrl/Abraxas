#!/usr/bin/env python3
"""Report the CI green streak on main, because "earn CI history" needs a number.

docs/BETA_READINESS.md names CI history as the one remaining gate on beta 1, and states it as
wall-clock rather than work. That is true, but it is also unmeasured: nothing in the repository says
how much history exists, so the gate can be neither claimed nor falsified. This turns it into a
reading.

Usage:
    python scripts/ci_history.py                 # every branch, default repo
    python scripts/ci_history.py --limit 100     # look further back
    python scripts/ci_history.py --json          # machine-readable

Exit codes: 0 always, unless gh fails. This is an instrument, not a gate: it reports, it does not
block. Making CI history a pass/fail gate would let a slow week block an unrelated merge, which is
the wrong shape for the thing being measured.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta

DEFAULT_WORKFLOW = "ci.yml"


def gh_json(args: list[str]) -> object:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"gh failed ({proc.returncode}): {proc.stderr.strip()}")
    return json.loads(proc.stdout or "[]")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow", default=DEFAULT_WORKFLOW)
    ap.add_argument("--branch", default="main")
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    runs = gh_json([
        "run", "list", "--workflow", args.workflow, "--branch", args.branch,
        "--limit", str(args.limit),
        "--json", "databaseId,conclusion,status,headSha,createdAt",
    ])
    if not isinstance(runs, list) or not runs:
        raise SystemExit(f"no runs found for {args.workflow} on {args.branch}")

    # gh returns newest first. The streak is the run of completed successes from the newest run
    # back to the first non-success, so an in-flight run at the head does not truncate it.
    considered = [r for r in runs if r.get("status") == "completed"]
    streak: list[dict] = []
    for r in considered:
        if r.get("conclusion") == "success":
            streak.append(r)
        else:
            break

    total = len(considered)
    success = sum(1 for r in considered if r.get("conclusion") == "success")
    in_flight = sum(1 for r in runs if r.get("status") != "completed")

    oldest = None
    if len(streak) > 1:
        oldest = min(datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")) for r in streak)
    elif streak:
        oldest = datetime.fromisoformat(streak[-1]["createdAt"].replace("Z", "+00:00"))

    now = datetime.now(oldest.tzinfo) if oldest else None
    span = now - oldest if (now and oldest) else timedelta(0)

    report = {
        "workflow": args.workflow,
        "branch": args.branch,
        "streak": len(streak),
        "completed_runs_seen": total,
        "successful_runs_seen": success,
        "in_flight": in_flight,
        "streak_started": oldest.isoformat() if oldest else None,
        "streak_span_hours": round(span.total_seconds() / 3600, 1),
        "head_sha": streak[0]["headSha"][:8] if streak else (runs[0]["headSha"][:8] if runs else None),
    }

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"  workflow          {report['workflow']} on {report['branch']}")
    print(f"  head              {report['head_sha']}")
    print(f"  green streak      {report['streak']} consecutive completed runs")
    if streak:
        print(f"  streak started    {report['streak_started']}")
        print(f"  span              {report['streak_span_hours']} hours")
    print(f"  window seen       {report['successful_runs_seen']}/{report['completed_runs_seen']} success"
          f"   ({report['in_flight']} in flight)")
    print()
    if report["streak"] < 2:
        print("  [JUDGEMENT] A streak of one is not history. The doc's gate is vertical, not")
        print("  horizontal: it needs time and real merges, neither of which this can manufacture.")
    elif report["streak_span_hours"] < 24:
        print("  [JUDGEMENT] Green, but under 24 hours of sustained runs. For beta this is early but directionally good.")
    else:
        print("  [JUDGEMENT] Sustained green history. Promotion preflight + real merges are the real gate now.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
