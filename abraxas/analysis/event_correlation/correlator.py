from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Set, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex

from .domains import infer_domain
from .windowing import stable_sort_envelopes, window_bounds


def _json_pointer_escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def resolve_pointer(doc: Any, pointer: str) -> Any:
    """
    RFC6901-ish JSON Pointer resolver (read-only).
    Returns None if any segment is missing / invalid.
    """
    if pointer == "":
        return doc
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        return None
    cur: Any = doc
    for raw in pointer.split("/")[1:]:
        tok = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict):
            if tok not in cur:
                return None
            cur = cur[tok]
        elif isinstance(cur, list):
            try:
                idx = int(tok)
            except Exception:
                return None
            if idx < 0 or idx >= len(cur):
                return None
            cur = cur[idx]
        else:
            return None
    return cur


def _safe_preview(v: Any, max_len: int = 96) -> str:
    """
    Small, safe string preview for evidence. Never returns raw nested objects.
    """
    if v is None:
        s = "null"
    elif isinstance(v, (str, int, float, bool)):
        s = str(v)
    elif isinstance(v, list):
        s = f"list(len={len(v)})"
    elif isinstance(v, dict):
        s = f"object(keys={len(v)})"
    else:
        s = type(v).__name__
    s = s.replace("\n", " ").replace("\r", " ").strip()
    if len(s) > max_len:
        return s[: max_len - 1] + "…"
    return s


def _artifact_id(envelope: Dict[str, Any]) -> str:
    """
    Deterministic artifact_id extraction with content-based fallback.
    """
    for k in ("artifact_id", "run_id", "id"):
        v = envelope.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    # Fallback: stable content hash (first 16 hex chars)
    return sha256_hex(canonical_json(envelope))[:16]


@dataclass(frozen=True)
class Occurrence:
    artifact_id: str
    domain: str
    pointer: str
    value_preview: str


def _extract_tokens(envelope: Dict[str, Any]) -> Dict[str, List[Occurrence]]:
    """
    Extract motif-like tokens from a narrow, auditable pointer set.
    Returns token -> occurrences (with pointers + previews).
    """
    aid = _artifact_id(envelope)
    dom = infer_domain(envelope)

    out: Dict[str, List[Occurrence]] = defaultdict(list)

    # 1) Primary motifs
    motifs_ptr = "/symbolic_compression/motifs"
    motifs = resolve_pointer(envelope, motifs_ptr)
    if isinstance(motifs, list):
        for i, m in enumerate(motifs):
            if not isinstance(m, str) or not m.strip():
                continue
            tok = m.strip()
            out[tok].append(
                Occurrence(
                    artifact_id=aid,
                    domain=dom,
                    pointer=f"{motifs_ptr}/{i}",
                    value_preview=_safe_preview(tok),
                )
            )

    # 2) Domain signals (keys only, bounded, deterministic)
    scores_ptr = "/signal_layer/scores"
    scores = resolve_pointer(envelope, scores_ptr)
    if isinstance(scores, dict):
        items: List[Tuple[str, float]] = []
        for k, v in scores.items():
            if not isinstance(k, str) or not k.strip():
                continue
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                items.append((k.strip(), float(v)))
        # deterministic: sort by score desc, then key asc
        items.sort(key=lambda kv: (-kv[1], kv[0]))
        for k, _score in items[:3]:
            tok = f"signal:{k}"
            ptr = f"{scores_ptr}/{_json_pointer_escape(k)}"
            out[tok].append(
                Occurrence(
                    artifact_id=aid,
                    domain=dom,
                    pointer=ptr,
                    value_preview=_safe_preview(resolve_pointer(envelope, ptr)),
                )
            )

    # 3) Optional slang terms (if present)
    slang_ptr = "/slang/terms"
    slang_terms = resolve_pointer(envelope, slang_ptr)
    if isinstance(slang_terms, list):
        for i, t in enumerate(slang_terms):
            if not isinstance(t, str) or not t.strip():
                continue
            tok = f"slang:{t.strip()}"
            out[tok].append(
                Occurrence(
                    artifact_id=aid,
                    domain=dom,
                    pointer=f"{slang_ptr}/{i}",
                    value_preview=_safe_preview(t.strip()),
                )
            )

    # 4) Optional aalmanac patterns (if present)
    aal_ptr = "/aalmanac/patterns"
    aal_patterns = resolve_pointer(envelope, aal_ptr)
    if isinstance(aal_patterns, list):
        for i, p in enumerate(aal_patterns):
            if not isinstance(p, str) or not p.strip():
                continue
            tok = f"aal:{p.strip()}"
            out[tok].append(
                Occurrence(
                    artifact_id=aid,
                    domain=dom,
                    pointer=f"{aal_ptr}/{i}",
                    value_preview=_safe_preview(p.strip()),
                )
            )

    return out


def _build_cooccurrence_graph(
    envelopes: Sequence[Dict[str, Any]],
    window_size: int,
    edge_min_count: int,
) -> Tuple[Dict[str, Set[str]], Dict[Tuple[str, str], int]]:
    """
    Co-occurrence graph over extracted tokens.

    v0.1 semantics (high auditability):
    - We count co-occurrence only when two motifs appear in the SAME envelope.
    - The rolling-window machinery is reserved for future upgrades (lead/lag, lagged co-occurrence),
      but for now we keep clusters tight and explainable.
    """
    token_sets: List[Set[str]] = []
    token_occ: Dict[str, List[Occurrence]] = defaultdict(list)

    def _use_for_graph(tok: str) -> bool:
        # v0.1: cluster only "primary motifs" (unprefixed tokens).
        # Secondary tokens like "signal:*", "slang:*", "aal:*" stay evidence-only.
        return isinstance(tok, str) and (":" not in tok)

    for env in envelopes:
        extracted = _extract_tokens(env)
        s: Set[str] = {t for t in extracted.keys() if _use_for_graph(t)}
        token_sets.append(s)
        for tok, occs in extracted.items():
            token_occ[tok].extend(occs)

    edges: Dict[Tuple[str, str], int] = defaultdict(int)
    graph: Dict[str, Set[str]] = defaultdict(set)

    # Count within-envelope motif pairs (deduped per envelope)
    for s in token_sets:
        toks = sorted(s)
        for i in range(len(toks)):
            for j in range(i + 1, len(toks)):
                x, y = toks[i], toks[j]
                edges[(x, y)] += 1

    # Materialize adjacency with threshold
    for (x, y), c in edges.items():
        if c >= edge_min_count:
            graph[x].add(y)
            graph[y].add(x)

    return graph, edges


def _connected_components(graph: Mapping[str, Set[str]]) -> List[Set[str]]:
    seen: Set[str] = set()
    comps: List[Set[str]] = []
    for node in sorted(graph.keys()):
        if node in seen:
            continue
        stack = [node]
        comp: Set[str] = set()
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.add(cur)
            for nb in sorted(graph.get(cur, set())):
                if nb not in seen:
                    stack.append(nb)
        if comp:
            comps.append(comp)
    return comps


def _score_cluster(
    motifs: Sequence[str],
    occurrences_by_token: Mapping[str, Sequence[Occurrence]],
    total_artifacts: int,
) -> Tuple[float, float, List[str], List[Occurrence]]:
    """
    Returns: (strength_score, confidence, domains_involved, evidence_occurrences_sorted)
    """
    all_occs: List[Occurrence] = []
    domains: Set[str] = set()
    artifacts: Set[str] = set()
    for m in motifs:
        for occ in occurrences_by_token.get(m, ()):
            all_occs.append(occ)
            domains.add(occ.domain)
            artifacts.add(occ.artifact_id)

    # stable sort evidence occurrences (for deterministic truncation)
    all_occs.sort(key=lambda o: (o.artifact_id, o.pointer, o.domain))

    freq_norm = (len(artifacts) / max(1, total_artifacts)) if total_artifacts > 0 else 0.0
    spread_norm = min(1.0, len(domains) / 4.0)  # 4 is an arbitrary "enough domains" cap for v0.1

    strength = min(1.0, 0.7 * freq_norm + 0.3 * spread_norm)
    conf = min(1.0, 0.5 * spread_norm + 0.5 * (math.log1p(len(all_occs)) / math.log1p(20.0)))

    return strength, conf, sorted(domains), all_occs


def correlate(envelopes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    correlate(envelopes) -> drift_report_v1

    Laws:
    - Shadow-only: read-only; never mutates envelopes or any forecast artifacts.
    - Evidence pointers: every emitted cluster includes (artifact_id, pointer, value_preview).
    - Deterministic: stable sorting + canonical hashing.
    - Offline-first: pure in-memory.
    """
    envs = stable_sort_envelopes(envelopes)
    total = len(envs)

    # Collect occurrences (token -> occurrences)
    occ_by_token: Dict[str, List[Occurrence]] = defaultdict(list)
    for env in envs:
        extracted = _extract_tokens(env)
        for tok, occs in extracted.items():
            occ_by_token[tok].extend(occs)

    # Build rolling co-occurrence graph
    graph, _edge_counts = _build_cooccurrence_graph(envs, window_size=3, edge_min_count=2)
    comps = _connected_components(graph)

    clusters: List[Dict[str, Any]] = []
    for comp in comps:
        motifs = sorted(comp)
        strength, conf, domains, all_occs = _score_cluster(motifs, occ_by_token, total)

        # Filter: require at least 2 domains and at least 2 artifacts worth of evidence
        artifact_ids = sorted({o.artifact_id for o in all_occs})
        if len(domains) < 2 or len(artifact_ids) < 2:
            continue

        evidence_refs = [
            {"artifact_id": o.artifact_id, "pointer": o.pointer, "value_preview": o.value_preview}
            for o in all_occs[:20]
        ]

        # Deterministic cluster id from motif set
        cluster_id = "CL-" + sha256_hex(canonical_json({"motifs": motifs}))[:12]

        clusters.append(
            {
                "cluster_id": cluster_id,
                "domains_involved": domains,
                "shared_motifs": motifs,
                "strength_score": float(f"{strength:.6f}"),
                "confidence": float(f"{conf:.6f}"),
                "lead_lag": None,
                "evidence_refs": evidence_refs,
            }
        )

    # Stable cluster ordering: strongest first, then id
    clusters.sort(key=lambda c: (-c["strength_score"], -c["confidence"], c["cluster_id"]))

    return {
        "schema_version": "drift_report_v1",
        "window": window_bounds(envs),
        "clusters": clusters,
    }

