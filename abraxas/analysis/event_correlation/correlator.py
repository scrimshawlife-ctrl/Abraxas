from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from .domains import domain_for_pointer
from .windowing import compute_window, stable_sort_envelopes


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _json_pointer_escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _json_pointer_get(doc: Any, pointer: str) -> Any:
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


def _safe_get(doc: Dict[str, Any], pointer: str) -> Tuple[bool, Any]:
    try:
        return True, _json_pointer_get(doc, pointer)
    except Exception:
        return False, None


@dataclass(frozen=True)
class CorrelatorConfig:
    schema_version: str = "1.0.0"
    algorithm_id: str = "motif_cooccur_v0_1"
    max_clusters: int = 12
    max_motifs_per_cluster: int = 5
    max_evidence_refs: int = 12
    min_artifact_support: int = 2  # motif must appear in at least N artifacts to be eligible


# v0.1: keep extraction narrow & deterministic.
MOTIF_POINTER_CANDIDATES = [
    # "envelope"-style (list of {motif,strength})
    "/symbolic_compression/motifs",
    "/symbolic_compression/motifs_v2",
    "/motifs",
    "/motifs_v2",
    # Oracle v2 shaped (dict token->weight)
    "/compression/compressed_tokens",
]


def _artifact_id(env: Dict[str, Any]) -> Optional[str]:
    v = env.get("artifact_id") or env.get("id") or env.get("artifactId") or env.get("run_id")
    return str(v) if v else None


def _created_at(env: Dict[str, Any]) -> Optional[str]:
    v = env.get("created_at") or env.get("createdAt") or env.get("created_at_utc") or env.get("created_at_utc")
    return v if isinstance(v, str) and len(v) >= 10 else None


def _report_created_at(envelopes: List[Dict[str, Any]]) -> str:
    """
    Deterministic report 'created_at' (offline-first).
    Prefer max created_at within window; fall back to a fixed epoch-like string.
    """
    ts = [t for t in (_created_at(e) for e in envelopes) if t is not None]
    if ts:
        return sorted(ts)[-1]
    return "1970-01-01T00:00:00Z"


def _extract_motifs(env: Dict[str, Any]) -> List[Tuple[str, str, float]]:
    """
    Returns list of (pointer, motif_name, strength) extracted from env.
    Deterministic ordering is imposed later.
    """
    for ptr in MOTIF_POINTER_CANDIDATES:
        ok, val = _safe_get(env, ptr)
        if not ok:
            continue

        # list-of-dicts format
        if isinstance(val, list):
            out: List[Tuple[str, str, float]] = []
            for idx, item in enumerate(val):
                if not isinstance(item, dict):
                    continue
                motif = item.get("motif") or item.get("name") or item.get("token")
                strength = item.get("strength")
                if isinstance(motif, str) and isinstance(strength, (int, float)):
                    out.append((f"{ptr}/{idx}", motif.strip()[:64], float(strength)))
            return out

        # dict-of-weights format (token->float)
        if isinstance(val, dict):
            out = []
            for k, v in val.items():
                if not isinstance(k, str) or not isinstance(v, (int, float)):
                    continue
                out.append((f"{ptr}/{_json_pointer_escape(k)}", k.strip()[:64], float(v)))
            # ensure deterministic within-doc ordering
            out.sort(key=lambda t: (t[1], t[0]))
            return out

    return []


def correlate(
    envelopes: List[Dict[str, Any]],
    *,
    cfg: Optional[CorrelatorConfig] = None,
    commit: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = cfg or CorrelatorConfig()
    envs = stable_sort_envelopes(envelopes)

    # Input set hash: based on ordered artifact_ids + created_at (stable) + canonical minimal.
    input_fingerprint = []
    for e in envs:
        input_fingerprint.append(
            {
                "artifact_id": _artifact_id(e) or "",
                "created_at": _created_at(e) or "",
            }
        )
    input_set_hash = _hash_text(_canonical_json(input_fingerprint))[:16]

    # Build motif index: motif -> occurrences (artifact_id, pointer, strength)
    motif_index: Dict[str, List[Tuple[str, str, float]]] = {}
    motif_domains: Dict[str, Set[str]] = {}

    for e in envs:
        aid = _artifact_id(e)
        if not aid:
            continue
        for pointer, motif, strength in _extract_motifs(e):
            motif_index.setdefault(motif, []).append((aid, pointer, strength))
            motif_domains.setdefault(motif, set()).add(domain_for_pointer(pointer))

    # Filter motifs by support
    eligible_motifs = []
    for motif, occs in motif_index.items():
        support = len({aid for aid, _, _ in occs})
        if support >= cfg.min_artifact_support:
            eligible_motifs.append(motif)

    # Score motifs: frequency + cross-domain spread bonus (simple, bounded)
    scored = []
    total_artifacts = max(1, len({(_artifact_id(e) or "") for e in envs if _artifact_id(e)}))
    for motif in eligible_motifs:
        occs = motif_index[motif]
        support = len({aid for aid, _, _ in occs})
        freq = support / total_artifacts  # 0..1
        domains = motif_domains.get(motif, {"unknown"})
        spread_bonus = min(1.0, (len(domains) - 1) * 0.25)  # 0, .25, .5, .75, 1.0...
        strength = max(0.0, min(1.0, freq * 0.75 + spread_bonus * 0.25))
        scored.append((strength, motif))

    # Deterministic: sort by strength desc then motif asc
    scored.sort(key=lambda t: (-t[0], t[1]))

    clusters = []
    used_motifs: Set[str] = set()

    # v0.1 clustering: each cluster anchored by a top motif; add co-occurring motifs within same artifacts
    for base_strength, base_motif in scored:
        if base_motif in used_motifs:
            continue

        base_occs = motif_index.get(base_motif, [])
        if not base_occs:
            continue
        base_artifacts = {aid for aid, _, _ in base_occs}

        # Find candidate motifs that co-occur in those artifacts
        co = []
        for s, motif in scored:
            if motif == base_motif or motif in used_motifs:
                continue
            occ_artifacts = {aid for aid, _, _ in motif_index.get(motif, [])}
            inter = len(base_artifacts.intersection(occ_artifacts))
            if inter >= 2:
                # Co-occur score: intersection proportion weighted by motif score
                co_score = (inter / max(1, len(base_artifacts))) * 0.5 + s * 0.5
                co.append((co_score, motif))
        co.sort(key=lambda t: (-t[0], t[1]))

        shared = [base_motif] + [m for _, m in co[: (cfg.max_motifs_per_cluster - 1)]]
        for m in shared:
            used_motifs.add(m)

        # Domains involved: union of domains from motif pointers
        domains_involved: Set[str] = set()
        evidence_refs = []

        for motif in shared:
            for aid, ptr, _strength in motif_index.get(motif, []):
                domains_involved.add(domain_for_pointer(ptr))
                evidence_refs.append({"artifact_id": aid, "pointer": ptr, "value_preview": motif})

        # Deterministic evidence selection: sort then truncate
        evidence_refs.sort(key=lambda r: (r["artifact_id"], r["pointer"], str(r.get("value_preview"))))
        evidence_refs = evidence_refs[: cfg.max_evidence_refs]

        # Cluster strength: base_strength plus mean of additional motif strengths (bounded)
        motif_strengths = []
        score_map = {m: s for s, m in scored}
        for motif in shared:
            motif_strengths.append(score_map.get(motif, 0.0))
        mean_s = sum(motif_strengths) / max(1, len(motif_strengths))
        strength_score = max(0.0, min(1.0, (base_strength * 0.6 + mean_s * 0.4)))

        # Confidence in v0.1: proportional to support and diversity (bounded)
        support_union = set()
        for motif in shared:
            support_union |= {aid for aid, _, _ in motif_index.get(motif, [])}
        support_ratio = len(support_union) / max(1, total_artifacts)
        diversity = min(1.0, (len(domains_involved) - 1) * 0.25)
        confidence = max(0.0, min(1.0, support_ratio * 0.7 + diversity * 0.3))

        cluster_id = _hash_text(base_motif + "|" + input_set_hash)[:12]

        clusters.append(
            {
                "cluster_id": cluster_id,
                "domains_involved": sorted(domains_involved) if domains_involved else ["unknown"],
                "shared_motifs": shared,
                "strength_score": strength_score,
                "confidence": confidence,
                "lead_lag": None,
                "evidence_refs": evidence_refs
                or [{"artifact_id": base_occs[0][0], "pointer": base_occs[0][1], "value_preview": base_motif}],
            }
        )

        if len(clusters) >= cfg.max_clusters:
            break

    window = compute_window(envs)

    report = {
        "schema_version": cfg.schema_version,
        "window": {
            "start_created_at": window.start_created_at,
            "end_created_at": window.end_created_at,
            "artifact_count": window.artifact_count,
        },
        "clusters": clusters,
        "provenance": {
            "created_at": _report_created_at(envs),
            "input_set_hash": input_set_hash,
            "algorithm_id": cfg.algorithm_id,
            "commit": commit,
        },
    }
    report["_canonical"] = _canonical_json(report)
    return report

