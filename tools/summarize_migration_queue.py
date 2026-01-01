import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_jsonl(path: str, limit: int = 50000):
    p = Path(path)
    if not p.exists():
        return []
    out = []
    with p.open("r", encoding="utf-8") as file:
        for index, line in enumerate(file):
            if index >= limit:
                break
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def summarize(
    audit_path: str = "data/audit_report.json",
    ledger_path: str = "data/rune_invocations.jsonl",
):
    audit = load_json(audit_path)
    findings = audit.get("findings", {}) or {}
    scores = audit.get("scores", {}) or {}

    invocations = read_jsonl(ledger_path)
    rune_counts = Counter(
        [record.get("rune_id") for record in invocations if record.get("rune_id")]
    )
    callsite_counts = Counter()
    for record in invocations:
        callsite = record.get("callsite", {}) or {}
        key = (
            f'{callsite.get("file", "?")}:'
            f'{callsite.get("line", "?")}:'
            f'{callsite.get("function", "?")}'
        )
        callsite_counts[key] += 1

    forbidden = findings.get("forbidden_actuation", []) or []
    cross = findings.get("cross_boundary_imports", []) or []
    detector = findings.get("detector_purity", []) or []

    queue = []
    for offender in forbidden[:50]:
        queue.append({"priority": 1, "type": "forbidden_actuation", **offender})
    for offender in cross[:200]:
        queue.append({"priority": 2, "type": "cross_boundary_import", **offender})
    for offender in detector[:200]:
        queue.append({"priority": 3, "type": "detector_purity", **offender})

    return {
        "scores": {
            "rune_invoke_ratio": scores.get("rune_invoke_ratio"),
            "cross_boundary_import_count": scores.get("cross_boundary_import_count"),
            "forbidden_actuation_count": scores.get("forbidden_actuation_count"),
            "detector_purity_violations": scores.get("detector_purity_violations"),
        },
        "top_runes": rune_counts.most_common(10),
        "top_callsites": callsite_counts.most_common(10),
        "migration_queue": queue[:50],
    }


if __name__ == "__main__":
    output = summarize()
    output_path = ROOT / "data" / "migration_queue.json"
    output_path.write_text(
        json.dumps(output, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(str(output_path))
