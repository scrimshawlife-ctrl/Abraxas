import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from abraxas.analysis.event_correlation.correlator import correlate


SRC_OUT = Path("out")
SRC_LEDGER = SRC_OUT / "ledger"
OUT = SRC_OUT / "drift_report_v1.json"


def _load_envs() -> list[dict]:
    envs: list[dict] = []

    # Prefer Oracle v2 ledger JSONL (common in this repo)
    oracle_runs = sorted(SRC_LEDGER.glob("oracle_runs_*.jsonl"))
    if oracle_runs:
        newest = oracle_runs[-1]
        for line in newest.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                envs.append(json.loads(line))
            except Exception:
                continue
        return envs

    # Fallback: scan JSON files under out/
    for p in sorted(SRC_OUT.rglob("*.json")):
        try:
            env = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # crude filter: only include things that look like envelopes
        if any(k in env for k in ("artifact_id", "run_id", "created_at", "created_at_utc", "symbolic_compression", "compression")):
            envs.append(env)

    return envs


def main() -> None:
    envs = _load_envs()
    if not envs:
        raise SystemExit("No envelope-like artifacts found under out/")

    report = correlate(envs)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()

