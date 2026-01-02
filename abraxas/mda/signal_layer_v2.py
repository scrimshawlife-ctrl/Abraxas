from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .types import sha256_hex, stable_json_dumps


@dataclass(frozen=True)
class SignalV2Config:
    """
    Evidence gating:
      - If no evidence refs exist for a DSP, we omit per-claim evidence details entirely.
      - We still allow counts and hashes.
    """

    emit_evidence: bool = True
    max_edges: int = 100
    max_events_per_dsp: int = 50


def _domain_key(d: str) -> str:
    return str(d or "unknown")


def _sub_key(sd: str) -> str:
    return str(sd or "unknown")


def _stable_edges(edges: List[Dict[str, Any]], *, max_edges: int) -> List[Dict[str, Any]]:
    es = sorted(edges, key=lambda e: (e.get("edge_type", ""), e.get("src_id", ""), e.get("dst_id", "")))
    out: List[Dict[str, Any]] = []
    for e in es[:max_edges]:
        out.append(
            {
                "edge_type": str(e.get("edge_type")),
                "src_id": str(e.get("src_id")),
                "dst_id": str(e.get("dst_id")),
                "weight": float(e.get("weight", 1.0)),
            }
        )
    return out


def _stable_events(
    events: List[Dict[str, Any]],
    *,
    max_events: int,
    emit_evidence: bool,
    has_evidence: bool,
) -> List[Dict[str, Any]]:
    # deterministic: sort by time then event_id
    evs = sorted(events, key=lambda e: (e.get("time", ""), e.get("event_id", "")))
    out: List[Dict[str, Any]] = []
    for ev in evs[:max_events]:
        claims = ev.get("claims", []) or []
        # deterministic: sort claims by confidence desc then claim text
        claims_sorted = sorted(claims, key=lambda c: (-float(c.get("confidence", 0.0)), str(c.get("claim", ""))))
        claims_out: List[Dict[str, Any]] = []
        for c in claims_sorted:
            # Evidence gating: if DSP has no evidence, omit evidence_refs entirely (even if claim contains junk)
            co: Dict[str, Any] = {
                "claim": str(c.get("claim", "")),
                "confidence": float(c.get("confidence", 0.0)),
            }
            if emit_evidence and has_evidence:
                co["evidence_refs"] = [str(x) for x in (c.get("evidence_refs") or []) if str(x).strip()]
            claims_out.append(co)

        eo = {
            "event_id": str(ev.get("event_id", "")),
            "title": str(ev.get("title", "")),
            "time": str(ev.get("time", "")),
            "tags": [str(x) for x in (ev.get("tags") or []) if str(x).strip()],
            "claims": claims_out,
        }
        out.append(eo)
    return out


def mda_to_oracle_signal_v2(
    mda_out: Dict[str, Any],
    *,
    config: Optional[SignalV2Config] = None,
) -> Dict[str, Any]:
    """
    Project MDA output into Oracle Signal Layer v2.
    Shape is stable and deterministic; ordering is canonical.
    """
    cfg = config or SignalV2Config()

    env = mda_out.get("envelope", {}) or {}
    dsp = mda_out.get("dsp", []) or []
    fusion = mda_out.get("fusion_graph", {}) or {}
    aggs = mda_out.get("domain_aggregates", {}) or {}

    # Organize DSPs by domain/subdomain
    dsp_sorted = sorted(dsp, key=lambda d: (_domain_key(d.get("domain")), _sub_key(d.get("subdomain"))))

    dsp_items: List[Dict[str, Any]] = []
    for d in dsp_sorted:
        scores = d.get("scores", {}) or {}
        events = d.get("events", []) or []
        ev_refs = d.get("evidence_refs", []) or []
        has_evidence = len(ev_refs) > 0

        item: Dict[str, Any] = {
            "domain": _domain_key(d.get("domain")),
            "subdomain": _sub_key(d.get("subdomain")),
            "status": str(d.get("status")),
            "scores": {
                "impact": float(scores.get("impact", 0.0)),
                "velocity": float(scores.get("velocity", 0.0)),
                "uncertainty": float(scores.get("uncertainty", 1.0)),
                "polarity": float(scores.get("polarity", 0.0)),
            },
            "events_count": len(events),
            "evidence_count": len(ev_refs),
            "events": _stable_events(
                events,
                max_events=cfg.max_events_per_dsp,
                emit_evidence=cfg.emit_evidence,
                has_evidence=has_evidence,
            ),
        }
        # Evidence gating: include evidence_refs only if allowed AND present
        if cfg.emit_evidence and has_evidence:
            item["evidence_refs"] = [str(x) for x in ev_refs if str(x).strip()]
        dsp_items.append(item)

    # Aggregates stable order
    agg_items: List[Dict[str, Any]] = []
    for dom in sorted(aggs.keys()):
        a = aggs.get(dom) or {}
        s = a.get("scores", {}) or {}
        agg_items.append(
            {
                "domain": str(dom),
                "status": str(a.get("status")),
                "scores": {
                    "impact": float(s.get("impact", 0.0)),
                    "velocity": float(s.get("velocity", 0.0)),
                    "uncertainty": float(s.get("uncertainty", 1.0)),
                    "polarity": float(s.get("polarity", 0.0)),
                },
                "subdomains": list(a.get("subdomains", []) or []),
                "evidence_count": len(a.get("evidence_refs", []) or []),
            }
        )

    edges = fusion.get("edges", []) or []
    fusion_compact = {
        "nodes_count": len((fusion.get("nodes", {}) or {})),
        "edges_count": len(edges),
        "edges": _stable_edges(edges, max_edges=cfg.max_edges),
    }

    # Stable hash for the emitted slice (separate from mda_out)
    slice_hash = sha256_hex(
        stable_json_dumps(
            {
                "env": env,
                "dsp": dsp_items,
                "aggs": agg_items,
                "fusion": fusion_compact,
            }
        )
    )

    signal = {
        "oracle_signal_v2": {
            "meta": {
                "source": "abraxas.mda",
                "mda_version": "v1.1",
                "input_hash": env.get("input_hash"),
                "slice_hash": slice_hash,
            },
            "mda_v1_1": {
                "envelope": env,
                "domain_aggregates": agg_items,
                "dsp": dsp_items,
                "fusion": fusion_compact,
            },
        }
    }
    return signal


def shallow_schema_check(signal: Dict[str, Any]) -> None:
    """
    No external deps schema check.
    Ensures load-bearing keys exist with expected high-level types.
    """
    if "oracle_signal_v2" not in signal:
        raise ValueError("Missing oracle_signal_v2 root")
    osv2 = signal["oracle_signal_v2"]
    if "meta" not in osv2 or "mda_v1_1" not in osv2:
        raise ValueError("Missing meta or mda_v1_1")
    if not isinstance(osv2["mda_v1_1"].get("dsp"), list):
        raise ValueError("mda_v1_1.dsp must be list")
    if not isinstance(osv2["mda_v1_1"].get("domain_aggregates"), list):
        raise ValueError("mda_v1_1.domain_aggregates must be list")
    if not isinstance(osv2["mda_v1_1"].get("fusion"), dict):
        raise ValueError("mda_v1_1.fusion must be dict")

