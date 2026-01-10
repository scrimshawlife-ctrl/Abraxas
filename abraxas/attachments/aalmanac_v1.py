from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, List, Optional, TypedDict


class ProvenanceBundle(TypedDict):
    engine: str
    ruleset_id: str
    input_fingerprints: List[str]
    run_id: str
    determinism_hash: str


class AALmanacTermRecord(TypedDict):
    term: str
    term_type: str  # "single" | "compound"
    tokens: List[str]
    source_class: str
    domain_tags: List[str]
    sense_shift: Dict[str, Any]
    usage_frame: str
    example_templates: List[str]
    scores: Dict[str, float]
    half_life: str
    confidence: float
    provenance: ProvenanceBundle


class AALmanacSignalV1(TypedDict):
    schema_version: str
    generated_at_utc: str
    inputs_hash: str
    entries: List[AALmanacTermRecord]
    drift_ledger: List[Dict[str, Any]]
    provenance: ProvenanceBundle


@dataclass(frozen=True)
class AALmanacConfig:
    ruleset_id: str = "aalmanac.rules.v1"
    engine: str = "abraxas"
    lane: str = "shadow"
    max_entries: int = 24  # keep oracle readable; catalog can store full set elsewhere


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(obj: Any) -> str:
    # deterministic JSON encoding → hash
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _tokenize(term: str) -> List[str]:
    # deterministic, minimal tokenizer (no NLP dependency)
    # split on whitespace, strip punctuation edges
    raw = term.strip().replace("_", " ")
    parts = [p.strip(" \t\n\r.,;:!?\"'()[]{}<>") for p in raw.split()]
    return [p for p in parts if p]


def _term_type_from_tokens(tokens: List[str]) -> str:
    return "single" if len(tokens) == 1 else "compound"


def _enforce_token_contract(term: str, term_type: str, tokens: List[str]) -> Optional[str]:
    if term_type == "single" and len(tokens) != 1:
        return f"single_term_token_violation:{term}"
    if term_type == "compound" and len(tokens) < 2:
        return f"compound_term_token_violation:{term}"
    return None


def build_aalmanac_attachment(
    *,
    seed_inputs: Dict[str, Any],
    raw_terms: List[Dict[str, Any]],
    cfg: AALmanacConfig = AALmanacConfig(),
) -> AALmanacSignalV1:
    """
    raw_terms: list of dicts from your slang engine / oracle extraction stage.
      Expected minimal fields: term, source_class, domain_tags, usage_frame, sense_shift, example_templates, scores, confidence, half_life
    Determinism: strict ordering + stable hashing.
    """
    # 1) Deterministic ordering: by (term_type, term) after tokenization
    normalized: List[AALmanacTermRecord] = []
    fingerprints: List[str] = []

    for t in raw_terms:
        term = str(t.get("term", "")).strip()
        if not term:
            continue

        tokens = t.get("tokens")
        if not tokens:
            tokens = _tokenize(term)
        tokens = [str(x) for x in tokens if str(x)]

        term_type = t.get("term_type") or _term_type_from_tokens(tokens)
        term_type = str(term_type)

        violation = _enforce_token_contract(term, term_type, tokens)
        if violation:
            # shadow-only: we drop invalid records and log fingerprint for drift debugging
            fingerprints.append(f"drop://{violation}")
            continue

        rec: AALmanacTermRecord = {
            "term": term,
            "term_type": term_type,
            "tokens": tokens,
            "source_class": str(t.get("source_class", "oracle_internal")),
            "domain_tags": [str(x) for x in (t.get("domain_tags") or ["culture"])],
            "sense_shift": dict(t.get("sense_shift") or {
                "from_sense": "unknown",
                "to_sense": "unknown",
                "shift_type": "compression",
            }),
            "usage_frame": str(t.get("usage_frame", "No frame provided.")),
            "example_templates": [str(x) for x in (t.get("example_templates") or [])][:6]
            or [f"Template: {term} in context."],
            "scores": dict(t.get("scores") or {"STI": 0.0, "CP": 0.0, "IPS": 0.0, "RFR": 0.0, "lambdaN": 0.0}),
            "half_life": str(t.get("half_life", "days")),
            "confidence": float(t.get("confidence", 0.5)),
            "provenance": {
                "engine": cfg.engine,
                "ruleset_id": cfg.ruleset_id,
                "input_fingerprints": [],  # filled later
                "run_id": "runtime",  # filled later
                "determinism_hash": "",  # filled later
            },
        }
        normalized.append(rec)

    normalized.sort(key=lambda r: (r["term_type"], r["term"].lower()))

    # 2) Cap for readability (catalog can store full elsewhere)
    entries = normalized[: cfg.max_entries]

    # 3) Build provenance + hashes
    inputs_hash = _stable_hash(seed_inputs)
    run_id = _stable_hash({"ts": _utc_now_iso(), "inputs_hash": inputs_hash})[:16]  # short deterministic-ish id per run
    base_prov: ProvenanceBundle = {
        "engine": cfg.engine,
        "ruleset_id": cfg.ruleset_id,
        "input_fingerprints": [inputs_hash] + fingerprints,
        "run_id": run_id,
        "determinism_hash": "",  # filled after envelope assembled
    }

    envelope: Dict[str, Any] = {
        "schema_version": "aalmanac.signal.v1",
        "generated_at_utc": _utc_now_iso(),
        "inputs_hash": inputs_hash,
        "entries": entries,
        "drift_ledger": [],  # populated by future drift comparator (separate rune)
        "provenance": base_prov,
    }

    det_hash = _stable_hash(envelope)
    envelope["provenance"]["determinism_hash"] = det_hash

    # stamp child prov with shared bundle (stable)
    for e in envelope["entries"]:
        e["provenance"] = base_prov

    return envelope  # type: ignore[return-value]
