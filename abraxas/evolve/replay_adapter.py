from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ReplayRun:
    ok: bool
    metrics_path: str
    metrics: Dict[str, float]
    stdout: str
    stderr: str
    exit_code: int
    notes: List[str]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _read_metrics(path: str) -> Dict[str, float]:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "metrics" in data and isinstance(data["metrics"], dict):
        data = data["metrics"]
    if not isinstance(data, dict):
        return {}
    out: Dict[str, float] = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            out[str(key)] = float(value)
    return out


def run_replay_command(
    *,
    run_id: str,
    policy_path: str,
    out_metrics_path: str,
    inputs_dir: Optional[str] = None,
    replay_cmd: Optional[str] = None,
    timeout_s: int = 300,
) -> ReplayRun:
    """
    Runs a user-provided replay command that must write metrics JSON to out_metrics_path.
    Command contract (minimum):
      <cmd> --run-id RUN --policy POLICY --out METRICS_JSON [--inputs-dir DIR]
    """
    cmd = replay_cmd or os.getenv("ABRAXAS_REPLAY_CMD", "").strip()
    if not cmd:
        return ReplayRun(
            ok=False,
            metrics_path=out_metrics_path,
            metrics={},
            stdout="",
            stderr="ABRAXAS_REPLAY_CMD not set; cannot run real replay.",
            exit_code=2,
            notes=["missing_replay_cmd"],
            provenance={"method": "command", "policy": policy_path},
        )

    argv = shlex.split(cmd)
    argv += ["--run-id", run_id, "--policy", policy_path, "--out", out_metrics_path]
    if inputs_dir:
        argv += ["--inputs-dir", inputs_dir]

    os.makedirs(os.path.dirname(out_metrics_path), exist_ok=True)

    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        metrics = _read_metrics(out_metrics_path)
        ok = (proc.returncode == 0) and bool(metrics)
        return ReplayRun(
            ok=ok,
            metrics_path=out_metrics_path,
            metrics=metrics,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            exit_code=int(proc.returncode),
            notes=[] if ok else ["replay_failed_or_empty_metrics"],
            provenance={"method": "command", "cmd": cmd, "policy": policy_path},
        )
    except subprocess.TimeoutExpired as exc:
        return ReplayRun(
            ok=False,
            metrics_path=out_metrics_path,
            metrics={},
            stdout=(exc.stdout or "") if hasattr(exc, "stdout") else "",
            stderr="Replay command timed out.",
            exit_code=124,
            notes=["timeout"],
            provenance={"method": "command", "cmd": cmd, "policy": policy_path},
        )


def metric_deltas(baseline: Dict[str, float], candidate: Dict[str, float]) -> Dict[str, float]:
    keys = sorted(set(baseline.keys()) | set(candidate.keys()))
    return {key: float(candidate.get(key, 0.0) - baseline.get(key, 0.0)) for key in keys}
