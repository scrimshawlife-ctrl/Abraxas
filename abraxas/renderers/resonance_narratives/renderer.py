from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .rules import NarrativeRules, default_rules, pointer_is_allowed, violates_forbidden_tokens


class NarrativeError(RuntimeError):
    pass


def _json_pointer_get(doc: Any, pointer: str) -> Any:
    """
    Minimal JSON Pointer resolver (RFC 6901-ish).
    Raises KeyError/IndexError on missing targets.
    """
    if pointer == "" or pointer == "/":
        return doc
    if not pointer.startswith("/"):
        raise ValueError(f"Invalid pointer: {pointer}")
    parts = pointer.lstrip("/").split("/")
    cur = doc
    for raw in parts:
        key = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            cur = cur[int(key)]
        else:
            cur = cur[key]
    return cur


def _json_pointer_escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_get(envelope: Dict[str, Any], pointer: str) -> Tuple[bool, Any]:
    try:
        return True, _json_pointer_get(envelope, pointer)
    except Exception:
        return False, None


@dataclass(frozen=True)
class RenderConfig:
    schema_version: str = "1.0.0"
    max_summary_items: int = 12
    max_motifs: int = 12
    max_changes: int = 10


def render(
    envelope_v2: Dict[str, Any],
    previous_envelope_v2: Optional[Dict[str, Any]] = None,
    *,
    rules: Optional[NarrativeRules] = None,
    cfg: Optional[RenderConfig] = None,
) -> Dict[str, Any]:
    rules = rules or default_rules()
    cfg = cfg or RenderConfig()

    # --- Required identity fields (prefer canonical top-level keys) ---
    artifact_id = (
        envelope_v2.get("artifact_id")
        or envelope_v2.get("id")
        or envelope_v2.get("artifactId")
        or envelope_v2.get("run_id")
    )
    if not artifact_id:
        raise NarrativeError("Envelope missing artifact_id (artifact_id/id/artifactId/run_id)")

    created_at = (
        envelope_v2.get("created_at")
        or envelope_v2.get("createdAt")
        or envelope_v2.get("created_at_utc")
        or envelope_v2.get("timestamp_utc")
        or _now_iso()
    )

    narrative_block = envelope_v2.get("narrative") if isinstance(envelope_v2.get("narrative"), dict) else {}
    input_hash = (
        envelope_v2.get("input_hash")
        or envelope_v2.get("inputHash")
        or narrative_block.get("bundle_hash")
        or "unknown"
    )

    # --- Constraints ---
    missing_inputs = envelope_v2.get("missing_inputs") or []
    not_computable = envelope_v2.get("not_computable") or []

    evidence_present = bool(
        envelope_v2.get("evidence") or envelope_v2.get("evidence_bundle") or envelope_v2.get("evidence_refs")
    )

    # --- Signal summary (pull stable numeric-ish scores if present) ---
    signal_summary: List[Dict[str, Any]] = []

    # Try a couple likely locations without assuming exact schema yet:
    candidate_score_pointers = [
        "/signal_layer/scores",
        "/signal_layer/scores_v2",
        "/scores",
        "/scores_v2",
        # Sample oracle run artifacts:
        "/compression/signal_strengths",
    ]
    scores_obj = None
    scores_ptr_used = None
    for ptr in candidate_score_pointers:
        ok, val = _safe_get(envelope_v2, ptr)
        if ok and isinstance(val, dict):
            scores_obj = val
            scores_ptr_used = ptr
            break

    if isinstance(scores_obj, dict) and isinstance(scores_ptr_used, str):
        # Keep deterministic ordering: sorted keys
        for k in sorted(scores_obj.keys())[: cfg.max_summary_items]:
            v = scores_obj[k]
            if isinstance(v, (int, float, str, bool)) or v is None:
                pointer = f"{scores_ptr_used}/{_json_pointer_escape(str(k))}"
                if pointer_is_allowed(pointer, rules):
                    signal_summary.append(
                        {
                            "label": str(k)[:64],
                            "value": v,
                            "delta": None,
                            "pointer": pointer,
                        }
                    )

    # --- Motifs (symbolic compression) ---
    motifs: List[Dict[str, Any]] = []
    motif_ptr_candidates = [
        "/symbolic_compression/motifs",
        "/symbolic_compression/motifs_v2",
        "/motifs",
        "/motifs_v2",
        # Sample oracle run artifacts:
        "/compression/compressed_tokens",
    ]
    motif_val = None
    motif_ptr_used = None
    for ptr in motif_ptr_candidates:
        ok, val = _safe_get(envelope_v2, ptr)
        if ok and (isinstance(val, list) or isinstance(val, dict)):
            motif_val = val
            motif_ptr_used = ptr
            break

    if isinstance(motif_val, list) and isinstance(motif_ptr_used, str):
        # Deterministic: stable sort by (strength desc, motif asc)
        normalized: List[Tuple[float, str, Any, int]] = []
        for i, item in enumerate(motif_val):
            if isinstance(item, dict):
                m = item.get("motif") or item.get("name") or item.get("token")
                s = item.get("strength")
                h = item.get("decay_halflife") or item.get("halflife")
                if isinstance(m, str) and isinstance(s, (int, float)):
                    normalized.append((float(s), m, h, i))
        normalized.sort(key=lambda t: (-t[0], t[1]))
        for s, m, h, idx in normalized[: cfg.max_motifs]:
            pointer = f"{motif_ptr_used}/{idx}"
            if pointer_is_allowed(pointer, rules):
                motifs.append(
                    {
                        "motif": m[:64],
                        "strength": max(0.0, min(1.0, float(s))),
                        "decay_halflife": float(h) if isinstance(h, (int, float)) else None,
                        "pointer": pointer,
                    }
                )

    if isinstance(motif_val, dict) and isinstance(motif_ptr_used, str):
        # Treat dict entries as motif → strength mapping (deterministic by key sort)
        normalized2: List[Tuple[float, str]] = []
        for k in sorted(motif_val.keys()):
            v = motif_val[k]
            if isinstance(k, str) and isinstance(v, (int, float)) and not isinstance(v, bool):
                normalized2.append((float(v), k))
        normalized2.sort(key=lambda t: (-t[0], t[1]))
        for s, m in normalized2[: cfg.max_motifs]:
            pointer = f"{motif_ptr_used}/{_json_pointer_escape(m)}"
            if pointer_is_allowed(pointer, rules):
                motifs.append(
                    {
                        "motif": m[:64],
                        "strength": max(0.0, min(1.0, float(s))),
                        "decay_halflife": None,
                        "pointer": pointer,
                    }
                )

    # --- What changed (diff mode) ---
    what_changed: List[Dict[str, Any]] = []
    if previous_envelope_v2 is not None:
        # Minimal, deterministic diff on a shortlist of pointers
        diff_targets = [
            "/signal_layer/scores",
            "/signal_layer/scores_v2",
            "/symbolic_compression/motifs",
            "/symbolic_compression/motifs_v2",
            "/compression/signal_strengths",
            "/compression/compressed_tokens",
        ]
        for ptr in diff_targets:
            ok_a, a = _safe_get(previous_envelope_v2, ptr)
            ok_b, b = _safe_get(envelope_v2, ptr)
            if not (ok_a or ok_b):
                continue
            if a != b:
                label = f"Change detected at {ptr}"
                if pointer_is_allowed(ptr, rules):
                    what_changed.append(
                        {
                            "label": label,
                            "pointer": ptr,
                            "before": a if ok_a else None,
                            "after": b if ok_b else None,
                        }
                    )
            if len(what_changed) >= cfg.max_changes:
                break

    # --- Overlay notes (strictly tagged) ---
    overlay_notes: List[Dict[str, Any]] = []
    overlay = envelope_v2.get("interpretive_overlay") or envelope_v2.get("overlay")
    if isinstance(overlay, dict):
        # keep it conservative and deterministic
        text = overlay.get("summary") or overlay.get("note")
        if isinstance(text, str) and text.strip():
            t = text.strip()
            # Avoid causal language unless you explicitly allow it
            if violates_forbidden_tokens(t, rules) and not evidence_present:
                t = "Overlay present, but causal phrasing suppressed due to missing evidence."
            overlay_notes.append({"tag": "overlay", "text": t[:400]})
    elif isinstance(overlay, str) and overlay.strip():
        t = overlay.strip()
        if violates_forbidden_tokens(t, rules) and not evidence_present:
            t = "Overlay present, but causal phrasing suppressed due to missing evidence."
        overlay_notes.append({"tag": "overlay", "text": t[:400]})

    # --- Headline (deterministic composition) ---
    headline_bits: List[str] = []
    if signal_summary:
        # pick top 1–2 keys deterministically
        headline_bits.append(f"Signals: {signal_summary[0]['label']}")
        if len(signal_summary) > 1:
            headline_bits.append(f"+ {signal_summary[1]['label']}")
    if motifs:
        headline_bits.append(f"Motif: {motifs[0]['motif']}")
    if not headline_bits:
        headline_bits.append("Resonance Narrative")
    headline = " | ".join(headline_bits)[:180]

    bundle: Dict[str, Any] = {
        "schema_version": cfg.schema_version,
        "artifact_id": str(artifact_id),
        "headline": headline,
        "signal_summary": signal_summary,
        "what_changed": what_changed,
        "motifs": motifs,
        "overlay_notes": overlay_notes,
        "constraints_report": {
            "missing_inputs": list(missing_inputs) if isinstance(missing_inputs, list) else [],
            "not_computable": list(not_computable) if isinstance(not_computable, list) else [],
            "evidence_present": evidence_present,
        },
        "provenance_footer": {
            "created_at": str(created_at),
            "input_hash": str(input_hash),
            "source_count": envelope_v2.get("source_count"),
            "commit": envelope_v2.get("commit"),
        },
    }

    # Determinism check hook for internal use (not emitted; schema is additionalProperties:false)
    _ = _canonical_json(bundle)

    return bundle

