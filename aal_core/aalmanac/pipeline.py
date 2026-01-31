from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import hashlib
import json
import time

from aal_core.aalmanac.canonicalize import canonicalize, classify_term_from_raw
from aal_core.aalmanac.drift import compute_drift
from aal_core.aalmanac.filter import quality_gate, rejection_reason
from aal_core.aalmanac.mutation import detect_mutation, load_reference_dictionary
from aal_core.aalmanac.storage.entries import append_entry, load_entries
from aal_core.aalmanac.storage.rejections import append_rejection
from aal_core.aalmanac.oracle_attachment import build_oracle_attachment_with_rejections
from aal_core.aalmanac.scoring import derive_signals

DEFAULT_LOG_DIR = Path.home() / ".aal" / "logs" / "oracle"

_INTENT_MAP = {
    "context_shift": "context_shift",
    "neologism": "neologism",
    "clip": "semantic_narrowing",
    "blend": "orthographic_variant",
    "phonetic_flip": "phonetic_flip",
    "metaphor_bind": "metaphor_bind",
}


def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _context_shift_specific(proposal: Dict[str, Any]) -> bool:
    shift = proposal.get("context_shift", {}) or {}
    return any(
        str(shift.get(key, "")).strip()
        for key in ("domain_shift", "valence_shift", "scope_shift")
    )


def _entry_from_proposal(
    proposal: Dict[str, Any],
    *,
    run_id: str,
    lexicon: Iterable[str],
    now_utc: str,
) -> Dict[str, Any]:
    term_raw = str(proposal.get("term_raw", ""))
    classification = classify_term_from_raw(term_raw, declared_class=None)
    tokens = classification.tokens
    term_canonical = canonicalize(tokens)

    signals = proposal.get("signals", {}) or {}
    mutation_intent = str(proposal.get("intent", ""))
    mapped = _INTENT_MAP.get(mutation_intent, "context_shift")
    mutation_type = mapped

    lex_mutation = detect_mutation(term_canonical, lexicon=lexicon)
    if lex_mutation == "context_shift":
        mutation_type = "context_shift"

    metrics = proposal.get("metrics", {}) or {}
    base_term = str(proposal.get("base_term", "") or "")
    if base_term and base_term.lower() in {str(x).lower() for x in lexicon}:
        metrics.setdefault("base_term_exists", 1.0)
    derived_signals = derive_signals(term_raw, base_term, metrics=metrics)
    derived_signals["novelty"] = float(signals.get("novelty", 0.0) or 0.0)

    entry = {
        "schema_version": "aal.aalmanac.entry.v1_2",
        "entry_id": _sha256({"term": term_canonical, "run_id": run_id, "ts": now_utc}),
        "term_raw": term_raw,
        "term_canonical": term_canonical,
        "term_class": classification.term_class,
        "sense_id": _sha256({"term": term_canonical, "sense": proposal.get("suggested_senses", [])}),
        "definition": str((proposal.get("suggested_senses") or [{}])[0].get("sense", "")),
        "usage_context": {
            "domain": str((proposal.get("suggested_senses") or [{}])[0].get("domain", "")),
            "subdomain": str((proposal.get("suggested_senses") or [{}])[0].get("subdomain", "")),
            "register": str((proposal.get("suggested_senses") or [{}])[0].get("register", "casual")),
            "valence": str((proposal.get("suggested_senses") or [{}])[0].get("valence", "neutral")),
            "example_utterances": (proposal.get("suggested_senses") or [{}])[0].get(
                "example_utterances", []
            ),
        },
        "mutation_type": mutation_type,
        "signals": {
            **derived_signals,
            "source_fingerprint": proposal.get("evidence", {}).get("handles", []),
            "co_occurring_handles": proposal.get("evidence", {}).get("co_occurrence", []),
        },
        "drift": {
            "drift_charge": float(proposal.get("drift", {}).get("drift_charge", 0.0) or 0.0),
            "delta_from_prior": float(proposal.get("drift", {}).get("delta_from_prior", 0.0) or 0.0),
            "half_life_days": float(proposal.get("drift", {}).get("half_life_days", 30.0) or 30.0),
        },
        "provenance": {
            "run_id": run_id,
            "generator": "aal_core.aalmanac.pipeline",
            "deterministic": True,
            "seed": int(proposal.get("seed", 0) or 0),
            "inputs_hash": _sha256(proposal),
            "notes": classification.note or "",
        },
        "timestamps": {
            "first_seen_utc": now_utc,
            "last_seen_utc": now_utc,
        },
    }
    return entry


def _neologism_gate(entry: Dict[str, Any]) -> bool:
    signals = entry.get("signals", {}) or {}
    return (
        float(signals.get("plausibility", 0.0) or 0.0) >= 0.55
        and float(signals.get("compression_gain", 0.0) or 0.0) >= 0.50
        and float(signals.get("stickiness", 0.0) or 0.0) >= 0.60
    )


def _context_shift_gate(proposal: Dict[str, Any]) -> bool:
    return _context_shift_specific(proposal)


def mint_entries_from_slang(
    proposals_packet: Dict[str, Any],
    *,
    entries_path: Optional[Path] = None,
    rejections_path: Optional[Path] = None,
    lexicon_path: Optional[Path] = None,
) -> Dict[str, Any]:
    run_id = str((proposals_packet.get("provenance", {}) or {}).get("run_id", "unknown"))
    now_utc = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    lexicon = load_reference_dictionary(lexicon_path=lexicon_path)
    existing = load_entries(entries_path=entries_path)
    latest_by_term: Dict[str, Dict[str, Any]] = {}
    for entry in existing:
        term = str(entry.get("term_canonical", ""))
        if term:
            latest_by_term[term] = entry

    entries_delta: List[Dict[str, Any]] = []
    rejections: List[Dict[str, Any]] = []

    for proposal in proposals_packet.get("proposals", []) or []:
        entry = _entry_from_proposal(proposal, run_id=run_id, lexicon=lexicon, now_utc=now_utc)
        prior = latest_by_term.get(entry.get("term_canonical", ""))
        compute_drift(entry, prior_entry=prior)

        if entry.get("mutation_type") == "neologism" and not _neologism_gate(entry):
            reason = "neologism_gate_failed"
            append_rejection(entry, reason=reason, rejection_path=rejections_path)
            rejections.append({"entry": entry, "reason": reason})
            continue

        if entry.get("mutation_type") == "context_shift" and not _context_shift_gate(proposal):
            reason = "context_shift_not_specific"
            append_rejection(entry, reason=reason, rejection_path=rejections_path)
            rejections.append({"entry": entry, "reason": reason})
            continue

        if not quality_gate(entry):
            reason = rejection_reason(entry)
            append_rejection(entry, reason=reason, rejection_path=rejections_path)
            rejections.append({"entry": entry, "reason": reason})
            continue

        append_entry(entry, entries_path=entries_path)
        entries_delta.append(entry)

    attachment = build_oracle_attachment_with_rejections(entries_delta, rejections, run_id=run_id)

    log_path = DEFAULT_LOG_DIR / f"{run_id}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_record = {
        "schema_version": "aal.aalmanac.pipeline.v0",
        "ts_utc": now_utc,
        "run_id": run_id,
        "entries_delta": entries_delta,
        "rejections": [{"reason": r["reason"], "term": r["entry"].get("term_raw", "")} for r in rejections],
        "attachment": attachment,
        "attachment_hash": _sha256(attachment),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(log_record, sort_keys=True) + "\n")

    return {
        "entries_delta": entries_delta,
        "rejections": rejections,
        "attachment": attachment,
    }
