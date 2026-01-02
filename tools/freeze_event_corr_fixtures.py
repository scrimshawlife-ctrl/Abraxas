import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


SRC_OUT = Path("out")
SRC_LEDGER = SRC_OUT / "ledger"
DST = Path("tests/fixtures/event_correlation/envelopes")
DST.mkdir(parents=True, exist_ok=True)


def _write_env(i: int, data: dict) -> None:
    out = DST / f"env_{i:02d}.json"
    out.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Wrote", out)


def _freeze_from_oracle_jsonl(path: Path, n: int) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue

    if not rows:
        raise SystemExit(f"No JSON rows found in {path}")

    picked = rows[:n]
    for i, row in enumerate(picked, 1):
        _write_env(i, row)


def _main() -> None:
    # Prefer Oracle v2 ledger runs (JSONL), since this repo commonly stores runs as JSONL.
    oracle_runs = sorted(SRC_LEDGER.glob("oracle_runs_*.jsonl"))
    if oracle_runs:
        newest = oracle_runs[-1]  # lexicographically newest date-stamped file
        print("Freezing from", newest)
        _freeze_from_oracle_jsonl(newest, n=10)
        return

    # Fallback: legacy JSON artifacts under out/
    candidates = sorted(SRC_OUT.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise SystemExit("No JSON artifacts found in out/. Run Oracle first.")

    picked = candidates[:10]
    for i, p in enumerate(picked, 1):
        data = json.loads(p.read_text(encoding="utf-8"))
        _write_env(i, data)


if __name__ == "__main__":
    _main()

