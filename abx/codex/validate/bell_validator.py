from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from ..registry import Codex
from ..schemas import Rune


Severity = Literal["info", "warn", "error"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_text(s: str) -> str:
    h = hashlib.sha256()
    h.update(s.encode("utf-8"))
    return h.hexdigest()


@dataclass(frozen=True)
class BellValidatorConfig:
    # Deterministic heuristic thresholds (no ML, no randomness).
    # If >= 1 signal in each bucket is present → violation.
    require_all_three_buckets: bool = True
    severity_on_violation: Severity = "warn"
    max_evidence_per_bucket: int = 5


@dataclass(frozen=True)
class BellFinding:
    finding_id: str
    severity: Severity
    subject_type: Literal["rune", "module"]
    subject_id: str
    title: str
    summary: str
    buckets: Dict[str, List[str]]  # locality/realism/hidden -> evidence strings
    recommendation: List[str]
    provenance: Dict[str, str]  # spec/created_utc/content_sha256


# --- Heuristic dictionaries (deterministic) ---

_LOCALITY_SIGNALS = (
    "strict module independence",
    "independent modules",
    "no cross-module coupling",
    "local-only",
    "purely local",
    "no global coupling",
    "factorizable",
    "separable",
)

_REALISM_SIGNALS = (
    "fixed meaning",
    "objective meaning",
    "pre-existing meaning",
    "static semantics",
    "symbol dictionary is ground truth",
    "context-independent meaning",
    "literal meaning only",
)

_HIDDEN_VAR_SIGNALS = (
    "hidden cause explains",
    "latent variable explains",
    "single root cause",
    "causal certainty",
    "deterministic latent",
    "explain away correlation",
    "the hidden variable is",
)


def _flatten_text_fields(obj: Any) -> List[str]:
    """
    Deterministically flatten nested dict/list primitives into text snippets.
    Only stringifies primitive leaves to avoid non-deterministic reprs.
    """
    out: List[str] = []

    def rec(x: Any) -> None:
        if x is None:
            return
        if isinstance(x, str):
            s = x.strip()
            if s:
                out.append(s)
            return
        if isinstance(x, (int, float, bool)):
            out.append(str(x))
            return
        if isinstance(x, dict):
            for k in sorted(x.keys(), key=lambda kk: str(kk)):
                rec(k)
                rec(x[k])
            return
        if isinstance(x, (list, tuple)):
            for item in x:
                rec(item)
            return
        # Ignore unknown types to keep determinism + avoid accidental leakage.
        return

    rec(obj)
    return out


def _collect_bucket_evidence(texts: Iterable[str], signals: Tuple[str, ...], cap: int) -> List[str]:
    hits: List[str] = []
    for t in texts:
        tl = t.lower()
        for s in signals:
            if s in tl:
                hits.append(f"match:{s} in:{t[:160]}")
                if len(hits) >= cap:
                    return hits
    return hits


def validate_bell_constraint(
    subject_type: Literal["rune", "module"],
    subject_id: str,
    payload: Dict[str, Any],
    cfg: Optional[BellValidatorConfig] = None,
) -> Optional[BellFinding]:
    """
    Returns a finding if Bell-violation pattern is detected.
    Pattern = evidence in all three buckets (locality, realism, hidden-var reductionism).
    """
    cfg = cfg or BellValidatorConfig()
    texts = _flatten_text_fields(payload)

    buckets: Dict[str, List[str]] = {
        "locality": _collect_bucket_evidence(texts, _LOCALITY_SIGNALS, cfg.max_evidence_per_bucket),
        "realism": _collect_bucket_evidence(texts, _REALISM_SIGNALS, cfg.max_evidence_per_bucket),
        "hidden": _collect_bucket_evidence(texts, _HIDDEN_VAR_SIGNALS, cfg.max_evidence_per_bucket),
    }

    has_all = bool(buckets["locality"]) and bool(buckets["realism"]) and bool(buckets["hidden"])
    has_any = bool(buckets["locality"] or buckets["realism"] or buckets["hidden"])

    if cfg.require_all_three_buckets and not has_all:
        return None
    if (not cfg.require_all_three_buckets) and not has_any:
        return None

    recs = [
        "Relax fixed semantic realism: require context-conditioned meaning resolution.",
        "Allow globally-coupled metrics for high-coherence events; avoid strict factorization.",
        "Downgrade latent-cause claims to provisional approximations; add explicit uncertainty tags.",
        "If insisting on locality, drop single-outcome realism (branch interpretations) or drop hidden-cause certainty.",
    ]

    finding_core = {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "buckets": buckets,
        "recs": recs,
    }
    content_hash = _sha256_text(json.dumps(finding_core, sort_keys=True, separators=(",", ":")))

    return BellFinding(
        finding_id=f"BELL_VIOLATION::{subject_type}::{subject_id}::{content_hash[:12]}",
        severity=cfg.severity_on_violation,
        subject_type=subject_type,
        subject_id=subject_id,
        title="Bell Constraint Violation Pattern Detected",
        summary=(
            "Design text appears to demand strict modular independence + fixed meaning + latent-cause certainty. "
            "This triple constraint is structurally incompatible with non-factorizable coherence."
        ),
        buckets=buckets,
        recommendation=recs,
        provenance={
            "spec": "abx.codex.validator.bell.v1",
            "created_utc": _utc_now_iso(),
            "content_sha256": content_hash,
        },
    )


def validate_codex_bell(codex: Codex, cfg: Optional[BellValidatorConfig] = None) -> List[BellFinding]:
    """
    Deterministic scan over codex runes (and future module manifests if wired).
    """
    cfg = cfg or BellValidatorConfig()
    findings: List[BellFinding] = []

    # Scan runes
    for rune_id in sorted(codex.runes.keys()):
        r: Rune = codex.runes[rune_id]
        payload = {
            "rune_id": r.rune_id,
            "name": r.name,
            "family": r.family,
            "version": r.version,
            "bindings": r.bindings,
            "canon_refs": r.canon_refs,
        }
        f = validate_bell_constraint("rune", rune_id, payload, cfg)
        if f is not None:
            findings.append(f)

    return findings
