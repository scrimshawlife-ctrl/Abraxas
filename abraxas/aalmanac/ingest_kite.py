"""
AALmanac KITE Export Consumer (Shadow Lane)
- Reads KITE export bundles (manifest.json + items.jsonl)
- Extracts candidate terms (single + compound)
- Writes deterministic candidate log for admin review
LOCAL ONLY. SHADOW ONLY. No promotion.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

_WORD = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9'\-]{1,}")
_STOP = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "if",
    "then",
    "so",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "at",
    "by",
    "from",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
}


@dataclass(frozen=True)
class Candidate:
    term: str
    kind: str
    score: float
    evidence_item_id: str
    tags: Tuple[str, ...]
    created_utc: str


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _normalize_term(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def _tokenize(text: str) -> List[str]:
    tokens = [m.group(0).lower() for m in _WORD.finditer(text)]
    return [t for t in tokens if t not in _STOP]


def _ngrams(tokens: List[str], n: int) -> Iterable[str]:
    if len(tokens) < n:
        return []
    return (" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def _score_term(term: str, kind: str, tags: Tuple[str, ...]) -> float:
    base = 0.5
    if kind == "compound":
        base += 0.2
    if any(tag in {"finance", "markets", "crypto", "ai", "geopolitics"} for tag in tags):
        base += 0.1
    base += min(0.2, 0.02 * max(0, len(term.split()) - 1))
    return round(min(0.99, base), 3)


def extract_candidates_from_item(item: Dict[str, Any]) -> List[Candidate]:
    tags = tuple(sorted({str(t).strip().lower() for t in item.get("tags", []) if str(t).strip()}))
    created_utc = str(item.get("created_utc", ""))
    item_id = str(item.get("item_id", ""))

    if item.get("type") != "text":
        return []

    text = item.get("content", {}).get("text", "") or ""
    tokens = _tokenize(text)

    freq: Dict[str, int] = {}
    for token in tokens:
        freq[token] = freq.get(token, 0) + 1

    singles = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:30]
    compounds: List[str] = []

    for n in (2, 3):
        for gram in _ngrams(tokens, n):
            if any(w in _STOP for w in gram.split()):
                continue
            compounds.append(gram)

    compounds_unique = sorted(set(compounds))

    out: List[Candidate] = []

    for term, _count in singles:
        normalized = _normalize_term(term)
        score = _score_term(normalized, "single", tags)
        out.append(
            Candidate(
                term=normalized,
                kind="single",
                score=score,
                evidence_item_id=item_id,
                tags=tags,
                created_utc=created_utc,
            )
        )

    for term in compounds_unique[:60]:
        normalized = _normalize_term(term)
        score = _score_term(normalized, "compound", tags)
        out.append(
            Candidate(
                term=normalized,
                kind="compound",
                score=score,
                evidence_item_id=item_id,
                tags=tags,
                created_utc=created_utc,
            )
        )

    return out


def ingest_kite_export(export_dir: Path, out_jsonl: Path) -> Dict[str, Any]:
    export_dir = Path(export_dir)
    manifest_path = export_dir / "manifest.json"
    items_path = export_dir / "items.jsonl"

    if not manifest_path.exists() or not items_path.exists():
        raise FileNotFoundError(f"Missing KITE export files in: {export_dir}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates: List[Candidate] = []
    with items_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            candidates.extend(extract_candidates_from_item(item))

    candidates.sort(key=lambda c: (c.created_utc, c.term, c.kind, c.evidence_item_id))

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("a", encoding="utf-8") as out:
        for candidate in candidates:
            obj = {
                "schema": "aalmanac.candidate.v0",
                "candidate_id": "sha256:" + _sha256(
                    f"{candidate.term}|{candidate.kind}|{candidate.evidence_item_id}"
                ),
                "term": candidate.term,
                "kind": candidate.kind,
                "score": candidate.score,
                "evidence_item_id": candidate.evidence_item_id,
                "tags": list(candidate.tags),
                "created_utc": candidate.created_utc,
                "source_export_id": manifest.get("export_id", ""),
            }
            out.write(json.dumps(obj, sort_keys=True) + "\n")

    return {
        "ingested_export": str(export_dir),
        "out_jsonl": str(out_jsonl),
        "candidate_count": len(candidates),
        "schema": "aalmanac.ingest_report.v0",
    }
