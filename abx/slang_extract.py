from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List


WORD = re.compile(r"[A-Za-z][A-Za-z0-9_\-']{2,}")
HASHTAG = re.compile(r"#[A-Za-z0-9_]{2,}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                if isinstance(d, dict):
                    out.append(d)
            except Exception:
                continue
    return out


def _append_jsonl(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _norm(tok: str) -> str:
    return (tok or "").strip()


def _features(term: str) -> Dict[str, float]:
    t = term
    return {
        "len": float(len(t)),
        "has_hyphen": 1.0 if "-" in t else 0.0,
        "has_underscore": 1.0 if "_" in t else 0.0,
        "has_digit": 1.0 if any(c.isdigit() for c in t) else 0.0,
        "camel": 1.0 if (re.search(r"[a-z][A-Z]", t) is not None) else 0.0,
        "allcaps": 1.0 if (t.isupper() and len(t) >= 4) else 0.0,
        "has_apostrophe": 1.0 if "'" in t else 0.0,
        "hashtag": 1.0 if t.startswith("#") else 0.0,
    }


def _score(term: str, c: int, baseline: Counter) -> float:
    """
    Emergence score (shadow): frequency + novelty + weirdness.
    """
    freq = min(1.0, c / 12.0)
    novelty = 1.0 if baseline.get(term.lower(), 0) == 0 else 0.0
    feat = _features(term)
    weird = 0.0
    weird += 0.15 * feat["has_hyphen"]
    weird += 0.15 * feat["has_digit"]
    weird += 0.10 * feat["camel"]
    weird += 0.10 * feat["hashtag"]
    weird += 0.10 * feat["allcaps"]
    weird += 0.08 * feat["has_apostrophe"]
    weird += 0.05 * feat["has_underscore"]
    return float(min(1.0, 0.55 * freq + 0.30 * novelty + 0.15 * min(1.0, weird)))


def _extract_terms(text: str) -> List[str]:
    out = []
    for m in WORD.finditer(text or ""):
        out.append(_norm(m.group(0)))
    for m in HASHTAG.finditer(text or ""):
        out.append(_norm(m.group(0)))
    return out


def _ngrams(tokens: List[str], n: int) -> Iterable[str]:
    if n <= 1:
        for t in tokens:
            yield t
        return
    for i in range(0, max(0, len(tokens) - n + 1)):
        yield " ".join(tokens[i : i + n])


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Extract slang candidates from oracle runs ledger"
    )
    ap.add_argument("--oracle-ledger", default="out/ledger/oracle_runs.jsonl")
    ap.add_argument("--anchor-ledger", default="out/ledger/anchor_ledger.jsonl")
    ap.add_argument(
        "--scan-anchors",
        action="store_true",
        default=True,
        help="Also scan anchor titles/content_hints",
    )
    ap.add_argument("--baseline-lexicon", default="out/config/baseline_lexicon.json")
    ap.add_argument("--out-ledger", default="out/ledger/slang_candidates.jsonl")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--min-score", type=float, default=0.45)
    ap.add_argument("--max-per-run", type=int, default=50)
    args = ap.parse_args()

    baseline = Counter()
    if os.path.exists(args.baseline_lexicon):
        try:
            with open(args.baseline_lexicon, "r", encoding="utf-8") as f:
                obj = json.load(f)
            if isinstance(obj, dict):
                baseline.update(
                    {str(k).lower(): int(v) for k, v in obj.items() if k}
                )
        except Exception:
            baseline = Counter()

    runs = [r for r in _read_jsonl(args.oracle_ledger) if r.get("kind") == "oracle_run"]
    anchors = _read_jsonl(args.anchor_ledger) if args.scan_anchors else []
    if not runs and not anchors:
        print("[SLANG] no oracle runs or anchors found")
        return 0

    emitted = 0
    for r in runs[-200:]:
        txt = str(r.get("text") or "")
        oracle_id = str(r.get("oracle_id") or "")
        if not txt or not oracle_id:
            continue

        tokens = _extract_terms(txt)
        grams = []
        grams.extend(list(_ngrams(tokens, 1)))
        grams.extend(list(_ngrams(tokens, 2)))
        grams.extend(list(_ngrams(tokens, 3)))

        counts = Counter(grams)
        scored = []
        for term, c in counts.items():
            if len(term) < 3:
                continue
            s = _score(term, int(c), baseline)
            if s >= float(args.min_score):
                scored.append((s, term, c))
        scored.sort(key=lambda x: (-x[0], x[1]))

        for s, term, c in scored[: int(args.max_per_run)]:
            obj = {
                "kind": "slang_candidate",
                "ts": _utc_now_iso(),
                "run_id": args.run_id,
                "oracle_id": oracle_id,
                "source_kind": "oracle_run",
                "term": term,
                "count_in_run": int(c),
                "score": float(s),
                "features": _features(term),
                "status": "SHADOW",
                "notes": "Candidate extracted deterministically from oracle runs; must be promoted into AAlmanac via governance.",
            }
            _append_jsonl(args.out_ledger, obj)
            emitted += 1

    if args.scan_anchors and anchors:
        for a in anchors[-400:]:
            title = str(a.get("title") or "")
            hint = str(a.get("content_hint") or "")
            anchor_id = str(a.get("anchor_id") or "")
            claim_id = str(a.get("claim_id") or "")
            domain = str(a.get("domain") or "")
            blob = f"{title}\n{hint}"
            if not blob.strip():
                continue
            tokens = _extract_terms(blob)
            grams = []
            grams.extend(list(_ngrams(tokens, 1)))
            grams.extend(list(_ngrams(tokens, 2)))
            grams.extend(list(_ngrams(tokens, 3)))
            counts = Counter(grams)
            scored = []
            for term, c in counts.items():
                if len(term) < 3:
                    continue
                s = _score(term, int(c), baseline)
                if s >= float(args.min_score):
                    scored.append((s, term, c))
            scored.sort(key=lambda x: (-x[0], x[1]))

            for s, term, c in scored[: int(args.max_per_run)]:
                obj = {
                    "kind": "slang_candidate",
                    "ts": _utc_now_iso(),
                    "run_id": args.run_id,
                    "oracle_id": "",
                    "source_kind": "anchor",
                    "anchor_id": anchor_id,
                    "claim_id": claim_id,
                    "domain": domain,
                    "term": term,
                    "count_in_run": int(c),
                    "score": float(s),
                    "features": _features(term),
                    "status": "SHADOW",
                    "notes": "Candidate extracted from anchor title/content_hint; must be promoted into AAlmanac via governance.",
                }
                _append_jsonl(args.out_ledger, obj)
                emitted += 1

    print(f"[SLANG] emitted candidates: {emitted} -> {args.out_ledger}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
