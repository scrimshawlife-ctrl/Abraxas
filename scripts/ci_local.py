#!/usr/bin/env python3
"""Run this repository's CI jobs locally, from CI's own step definitions.

WHY IT PARSES THE WORKFLOWS INSTEAD OF COPYING COMMANDS
    A hand-copied local runner drifts: CI gains a step, the copy does not. This reads
    .github/workflows/*.yml and executes each job's `run:` blocks in order, so the local result is
    the CI result by construction.

THE ONE THING THAT NEEDS TRANSLATING
    CI has `python` and `pytest` on PATH. Locally, bare `python3` on this machine resolves `core/`
    to an unrelated checkout and produces fake collection errors, and `pytest` may not be on PATH
    at all. So the runner creates a temporary bin directory holding exec-wrappers for `python`,
    `python3` and `pytest` that delegate to the interpreter you name, and prepends it to PATH.
    Wrappers, not symlinks: a symlink breaks virtualenv detection.

WHAT IT SKIPS, AND WHY IT SAYS SO
    Jobs that need GitHub event context (wip-limits, pr-automerge-docs) cannot run locally without
    fabricating an event. Jobs needing a tool this machine lacks are skipped loudly rather than
    silently passing. A skipped job is reported as skipped, never as a pass.

Usage:
    python scripts/ci_local.py                  # every runnable workflow
    python scripts/ci_local.py ci.yml           # one workflow
    PYTHON=/path/to/python python scripts/ci_local.py
"""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
import time

REPO = pathlib.Path(__file__).resolve().parents[1]
WORKFLOWS = REPO / ".github" / "workflows"

# Jobs whose steps need a GitHub event payload. Running them locally would mean inventing an event.
NEEDS_EVENT = {"wip-limits.yml", "pr-automerge-docs.yml"}

# Steps that are annotations/reporting and have no local meaning.
ADVISORY_HINTS = ("read-only visibility",)

WRAPPER_SOURCES = {
    "python": None,
    "python3": None,
    "pytest": "-m pytest",
}


def _parse_workflow(path: pathlib.Path):
    try:
        import yaml
    except ImportError:
        sys.exit("ci_local: PyYAML is required (pip install pyyaml)")
    try:
        return yaml.safe_load(path.read_text())
    except Exception as exc:
        print(f"  PARSE ERROR in {path.name}: {exc}")
        return None


def _make_bin_dir(interpreter: str) -> pathlib.Path:
    """A bin dir with exec-wrappers delegating to `interpreter`."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="ci-local-bin-"))
    for name, suffix in WRAPPER_SOURCES.items():
        target = f'exec "{interpreter}" {suffix} "$@"' if suffix else f'exec "{interpreter}" "$@"'
        wrapper = d / name
        wrapper.write_text(f"#!/bin/sh\n{target}\n")
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return d


def _required_tools(steps: list[str]) -> set[str]:
    """External tools a step needs, checked against PATH before running it."""
    tools = set()
    joined = "\n".join(steps)
    for tool in ("npm", "npx", "node", "gh", "ruff", "make", "bash", "docker"):
        if tool in joined:
            tools.add(tool)
    return tools


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("workflow", nargs="?", help="a single workflow file name")
    ap.add_argument("--list", action="store_true", help="list workflows and exit")
    args = ap.parse_args()

    if args.list:
        for wf in sorted(WORKFLOWS.glob("*.yml")):
            mark = " (needs event)" if wf.name in NEEDS_EVENT else ""
            print(f"  {wf.name}{mark}")
        return 0

    interpreter = os.environ.get("PYTHON", sys.executable)
    bin_dir = _make_bin_dir(interpreter)
    env = dict(os.environ)
    # Both the wrappers AND the interpreter's own bin directory go on PATH. CI has every tool of
    # the active environment available (ruff, for instance, lives beside the interpreter); with
    # only the wrapper dir prepended, steps that call such a tool fail for a reason that has
    # nothing to do with the repository.
    interp_bin = str(pathlib.Path(interpreter).resolve().parent)
    env["PATH"] = f"{bin_dir}{os.pathsep}{interp_bin}{os.pathsep}{env.get('PATH','')}"

    files = [WORKFLOWS / args.workflow] if args.workflow else sorted(WORKFLOWS.glob("*.yml"))
    results: list[tuple[str, str, str, float]] = []

    print(f"ci_local: interpreter = {interpreter}")
    print(f"ci_local: PATH prepended with {bin_dir}\n")

    for wf in files:
        if not wf.exists():
            print(f"  no such workflow: {wf.name}")
            continue
        if wf.name in NEEDS_EVENT:
            results.append((wf.name, "(workflow)", "SKIPPED needs GitHub event context", 0.0))
            print(f"=== {wf.name}: SKIPPED (needs GitHub event context) ===")
            continue

        doc = _parse_workflow(wf)
        if not doc:
            continue

        print(f"=== {wf.name} ===")
        for job_name, job in (doc.get("jobs") or {}).items():
            steps = [s for s in (job.get("steps") or []) if (s.get("run") or "").strip()]
            if not steps:
                continue

            runs = [s["run"] for s in steps]
            missing = {t for t in _required_tools(runs) if shutil.which(t, path=env["PATH"]) is None}
            if missing:
                label = f"{job_name} (missing: {', '.join(sorted(missing))})"
                results.append((wf.name, label, "SKIPPED missing tool", 0.0))
                print(f"  -- {label}: SKIPPED (missing {sorted(missing)})")
                continue

            for step in steps:
                name = step.get("name") or "(unnamed step)"
                advisory = any(h in name.lower() for h in ADVISORY_HINTS)
                # Per-job and per-step `env:` blocks must be honoured. CI's "Verify test count"
                # step takes its floor from `env: FLOOR: 3850`; ignoring that block made the step
                # die with "FLOOR: unbound variable", which looks like a repository failure and is
                # not one.
                step_env = dict(env)
                for source in (job.get("env") or {}, step.get("env") or {}):
                    step_env.update({k: str(v) for k, v in source.items()})
                t0 = time.time()
                proc = subprocess.run(
                    ["bash", "-c", step["run"]],
                    cwd=REPO, env=step_env, capture_output=True, text=True,
                )
                dt = time.time() - t0
                ok = proc.returncode == 0
                status = "PASS" if ok else "FAIL"
                if advisory and not ok:
                    status = "ADVISORY (non-fatal)"
                results.append((wf.name, f"{job_name} / {name}", status, dt))
                print(f"  [{status:<18}] {job_name} / {name}  ({dt:.1f}s)")
                if not ok:
                    tail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
                    for line in tail:
                        print(f"        | {line[:160]}")
        print()

    print("=" * 78)
    print("SUMMARY")
    fails = [r for r in results if r[2] == "FAIL"]
    for wf, step, status, _dt in results:
        print(f"  {status:<20} {wf}  ::  {step}")
    print()
    print(f"  steps: {len(results)}   pass: {sum(1 for r in results if r[2]=='PASS')}"
          f"   fail: {len(fails)}"
          f"   skipped: {sum(1 for r in results if r[2].startswith('SKIPPED'))}"
          f"   advisory: {sum(1 for r in results if r[2].startswith('ADVISORY'))}")
    shutil.rmtree(bin_dir, ignore_errors=True)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
