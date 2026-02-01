from __future__ import annotations

from typing import Any, Dict, List, Tuple
import json
import os

from .registry import DomainRegistryV1
from .types import FusionGraph, MDARunEnvelope, sha256_hex, stable_json_dumps


def run_mda(
    envelope: MDARunEnvelope, *, abraxas_version: str, registry: DomainRegistryV1
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Minimal deterministic MDA execution.

    Returns:
      - dsps: list of per-(domain,subdomain) deterministic projections
      - out: full payload dict suitable for artifact writing / replay / oracle bridge
    """
    vectors = (envelope.inputs or {}).get("vectors") or {}

    enabled_domains = set(envelope.enabled_domains)
    enabled_sub_keys = set(envelope.enabled_subdomains)

    dsps: List[Dict[str, Any]] = []
    for domain in registry.domains():
        if domain not in enabled_domains:
            continue
        for sub in registry.subdomains(domain):
            key = f"{domain}:{sub}"
            if key not in enabled_sub_keys:
                continue

            vec = None
            dom_vec = vectors.get(domain)
            if isinstance(dom_vec, dict):
                vec = dom_vec.get(sub)

            status = "ok" if vec is not None else "not_computable"
            scores = {"impact": 0, "velocity": 0, "uncertainty": 1, "polarity": 0}
            if isinstance(vec, dict) and isinstance(vec.get("scores"), dict):
                # keep only known score keys, deterministic defaults
                for k in list(scores.keys()):
                    if k in vec["scores"]:
                        scores[k] = vec["scores"][k]

            dsp = {
                "domain": domain,
                "subdomain": sub,
                "status": status,
                "window": {"from": envelope.run_at_iso, "to": envelope.run_at_iso},
                "scores": scores,
                "events": [] if not (isinstance(vec, dict) and isinstance(vec.get("events"), list)) else vec["events"],
                "evidence_refs": []
                if not (isinstance(vec, dict) and isinstance(vec.get("evidence_refs"), list))
                else vec["evidence_refs"],
                "provenance": {
                    "module": "abraxas.mda.run",
                    "version": str(abraxas_version),
                    "input_hash": envelope.input_hash(),
                    "run_seed": envelope.seed,
                },
            }
            dsps.append(dsp)

    # Stable ordering for hashing + reproducibility
    dsps = sorted(dsps, key=lambda d: (d.get("domain", ""), d.get("subdomain", "")))

    # Minimal fusion graph: deterministic nodes, no edges (add-only later).
    nodes = {f"{d['domain']}:{d['subdomain']}": {"status": d["status"]} for d in dsps}
    fusion_graph: FusionGraph = {"nodes": nodes, "edges": []}

    out: Dict[str, Any] = {
        "envelope": envelope.to_json(),
        "dsp": dsps,
        "fusion_graph": fusion_graph,
        "aggregates": {
            "dsp_count": len(dsps),
            "fusion_nodes": len(nodes),
            "fusion_edges": 0,
        },
        "out_hash": sha256_hex(stable_json_dumps({"dsp": dsps, "fusion_graph": fusion_graph})),
    }
    return dsps, out


def write_run_artifacts(out: Dict[str, Any], run_dir: str) -> None:
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "out.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, sort_keys=True)

