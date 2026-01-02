import json
from pathlib import Path

SRC_DIRS = [
    Path("out"),
    Path("data"),
]

DST = Path("tests/fixtures/resonance_narratives/envelopes")
DST.mkdir(parents=True, exist_ok=True)


def _read_json_any(p: Path):
    if p.suffix == ".json":
        return json.loads(p.read_text(encoding="utf-8"))
    if p.suffix == ".jsonl":
        # Deterministic pick: first non-empty line
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                return json.loads(line)
        raise SystemExit(f"JSONL file was empty: {p}")
    raise SystemExit(f"Unsupported file type: {p}")


def _candidates():
    out = []
    for d in SRC_DIRS:
        if not d.exists():
            continue
        out.extend(list(d.rglob("*.json")))
        out.extend(list(d.rglob("*.jsonl")))
    # prefer envelope-like names if present
    env_like = [p for p in out if "envelope" in p.name.lower()]
    return env_like or out


candidates = _candidates()
if not candidates:
    raise SystemExit("No JSON/JSONL artifacts found in out/ or data/.")

# Deterministic tie-break: (mtime desc, path asc)
picked = sorted(candidates, key=lambda p: (-p.stat().st_mtime, str(p)))[0]
data = _read_json_any(picked)

(DST / "envelope_01.json").write_text(
    json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print("Frozen fixture:", picked, "->", (DST / "envelope_01.json"))

