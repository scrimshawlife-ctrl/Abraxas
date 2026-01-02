from __future__ import annotations

from typing import Any, Dict, List, Tuple

import json

from .registry import DomainRegistryV1
from .types import DomainSignalPack, FusionEdge, FusionGraph, MDARunEnvelope, ScoreVector, sorted_unique_strs


def _load_fixture(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _default_scores(events: List[Dict[str, Any]]) -> ScoreVector:
    # Practice-run heuristic: deterministic, bounded, cheap.
    n = len(events)
    impact = 0.0 if n == 0 else min(1.0, n / 10.0)
    velocity = 0.0 if n < 2 else min(1.0, (n - 1) / 10.0)
    uncertainty = 1.0 if n == 0 else max(0.0, 1.0 - (n / 20.0))
    polarity = 0.0
    return ScoreVector(impact=impact, velocity=velocity, uncertainty=uncertainty, polarity=polarity)


def _coerce_events(node: Any) -> List[Dict[str, Any]]:
    if node is None:
        return []
    if isinstance(node, list):
        return [e for e in node if isinstance(e, dict)]
    if isinstance(node, dict):
        events = node.get("events", []) or []
        if isinstance(events, list):
            return [e for e in events if isinstance(e, dict)]
    return []


def _extract_scores(node: Any, events: List[Dict[str, Any]]) -> ScoreVector:
    if isinstance(node, dict):
        scores = node.get("scores")
        if isinstance(scores, dict):
            return ScoreVector(
                impact=float(scores.get("impact", 0.0)),
                velocity=float(scores.get("velocity", 0.0)),
                uncertainty=float(scores.get("uncertainty", 1.0)),
                polarity=float(scores.get("polarity", 0.0)),
            )
    return _default_scores(events)


def _extract_evidence_refs(node: Any, events: List[Dict[str, Any]]) -> Tuple[str, ...]:
    refs: List[str] = []
    if isinstance(node, dict):
        refs.extend([str(x) for x in (node.get("evidence_refs") or []) if str(x).strip()])

    # Also harvest evidence refs from nested claims if present.
    for ev in events:
        claims = ev.get("claims") or []
        if not isinstance(claims, list):
            continue
        for c in claims:
            if not isinstance(c, dict):
                continue
            refs.extend([str(x) for x in (c.get("evidence_refs") or []) if str(x).strip()])

    return sorted_unique_strs(refs)


def run_mda(
    envelope: MDARunEnvelope,
    abraxas_version: str,
    registry: DomainRegistryV1,
    *,
    domains: str | Tuple[str, ...] = "*",
    subdomains: str | Tuple[str, ...] = "*",
) -> Tuple[Tuple[DomainSignalPack, ...], Dict[str, Any]]:
    # Prefer in-memory inputs (v1.1 canary path). Fall back to fixture file if provided.
    if envelope.inputs and isinstance(envelope.inputs.get("vectors"), dict):
        vectors = envelope.inputs.get("vectors", {}) or {}
    elif envelope.fixture_path:
        fixture = _load_fixture(envelope.fixture_path)
        vectors = fixture.get("vectors", {}) or {}
    else:
        vectors = {}

    # Determine filtering contract:
    # - if the envelope declares enabled_* sets, use those
    # - else fall back to call-time params (legacy CLI)
    eff_domains: str | Tuple[str, ...] = envelope.enabled_domains if envelope.enabled_domains else domains
    eff_subdomains: str | Tuple[str, ...] = (
        envelope.enabled_subdomains if envelope.enabled_subdomains else subdomains
    )

    pairs = registry.filter_pairs(domains=eff_domains, subdomains=eff_subdomains)

    dsps: List[DomainSignalPack] = []
    domain_aggs: Dict[str, Any] = {}

    # Build DSPs.
    for dom, sub in pairs:
        node = (vectors.get(dom, {}) or {}).get(sub)
        events_list = _coerce_events(node)
        scores = _extract_scores(node, events_list)
        status = "ok" if events_list else "not_computable"
        evidence_refs = _extract_evidence_refs(node, events_list)
        dsps.append(
            DomainSignalPack(
                domain=dom,
                subdomain=sub,
                status=status,
                scores=scores,
                events=tuple(events_list),
                evidence_refs=evidence_refs,
            )
        )

        # Domain aggregate (simple rollup).
        # If multiple subdomains exist, keep the max impact / velocity and min uncertainty.
        agg = domain_aggs.get(dom)
        if agg is None:
            domain_aggs[dom] = {
                "status": status,
                "scores": scores.to_dict(),
            }
        else:
            cur = agg.get("scores", {}) or {}
            domain_aggs[dom] = {
                "status": "ok" if (agg.get("status") == "ok" or status == "ok") else "not_computable",
                "scores": {
                    "impact": max(float(cur.get("impact", 0.0)), scores.impact),
                    "velocity": max(float(cur.get("velocity", 0.0)), scores.velocity),
                    "uncertainty": min(float(cur.get("uncertainty", 1.0)), scores.uncertainty),
                    "polarity": float(cur.get("polarity", 0.0)),
                },
            }

    dsps_sorted = tuple(sorted(dsps, key=lambda d: (d.domain, d.subdomain)))

    # Build a deterministic fusion graph over DSP nodes.
    nodes: Dict[str, Dict[str, Any]] = {}
    for d in dsps_sorted:
        nid = f"dsp:{d.domain}:{d.subdomain}"
        nodes[nid] = {
            "kind": "dsp",
            "domain": d.domain,
            "subdomain": d.subdomain,
            "status": d.status,
        }

    edges: List[FusionEdge] = []
    node_ids = sorted(nodes.keys())
    for i in range(len(node_ids) - 1):
        src = node_ids[i]
        dst = node_ids[i + 1]
        edges.append(FusionEdge(src_id=src, dst_id=dst, edge_type="adjacent_dsp", weight=1.0))

    fusion = FusionGraph(nodes=nodes, edges=tuple(edges))

    out: Dict[str, Any] = {
        "envelope": {
            "env": envelope.env,
            "seed": envelope.seed,
            "run_at_iso": envelope.run_at_iso,
            "input_hash": envelope.input_hash(),
            "abraxas_version": abraxas_version,
        },
        "domain_aggregates": domain_aggs,
        "dsp": [d.to_dict() for d in dsps_sorted],
        "fusion_graph": fusion.to_dict(),
    }
    return dsps_sorted, out


def write_run_artifacts(payload: Dict[str, Any], run_dir: str) -> None:
    # Legacy helper kept for CLI usage (filesystem-writing practice runner).
    import os

    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "payload.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")

