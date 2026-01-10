from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.detectors.shadow.anagram import _norm_token_letters, _letter_counts


def _iso_now_fallback(run_at_iso: Optional[str]) -> str:
    if run_at_iso and str(run_at_iso).strip():
        return str(run_at_iso)
    # deterministic fallback is not allowed (time), so return a constant if missing
    return "1970-01-01T00:00:00Z"


def _key_from_norm(norm_letters: str) -> str:
    # Key = sha256 of counts vector (stable)
    counts = _letter_counts(norm_letters)
    blob = canonical_json({"counts": counts})
    return sha256_hex(blob)


@dataclass(frozen=True)
class ClusterBudgets:
    max_clusters: int = 200
    max_variants_per_cluster: int = 25
    max_src_tokens_per_cluster: int = 25
    max_domain_tags_per_cluster: int = 25
    max_watch_alerts: int = 25


@dataclass(frozen=True)
class ClusterConfig:
    budgets: ClusterBudgets = ClusterBudgets()
    # Burst heuristic: if count increases by >= burst_delta within same run window, flag
    burst_delta: int = 5
    # Watchlist tokens (raw). These are normalized to multiset keys deterministically.
    watchlist_tokens: Tuple[str, ...] = ()


def _stable_add_unique(lst: List[str], v: str, cap: int) -> None:
    if v in lst:
        return
    if len(lst) >= cap:
        return
    lst.append(v)


def init_cluster_state() -> Dict[str, Any]:
    """
    Deterministic initial state.
    """
    return {
        "version": "shadow_anagram_cluster_v1",
        "clusters": {},  # key -> cluster dict
        "global_count": 0,
        # watch: key -> {"token": raw, "last_variant_count": int}
        "watch": {},
    }

def _build_watch_map(tokens: Tuple[str, ...]) -> Dict[str, Dict[str, Any]]:
    w: Dict[str, Dict[str, Any]] = {}
    for t in tokens:
        raw = str(t).strip()
        if not raw:
            continue
        norm = _norm_token_letters(raw)
        if not norm:
            continue
        key = _key_from_norm(norm)
        # deterministically keep first token for a key (sorted by input order already from tuple)
        if key not in w:
            w[key] = {"token": raw, "last_variant_count": 0}
    return w


def update_anagram_clusters(
    state: Dict[str, Any],
    *,
    anagram_artifact: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
    run_at_iso: Optional[str] = None,
    config: Optional[ClusterConfig] = None,
) -> Dict[str, Any]:
    """
    Update cluster state from shadow_anagram_v1 output.
    Deterministic: no wall-clock time; uses run_at_iso or constant fallback.
    """
    cfg = config or ClusterConfig()
    budgets = cfg.budgets

    st = {
        "version": state.get("version", "shadow_anagram_cluster_v1"),
        "clusters": dict(state.get("clusters", {}) or {}),
        "global_count": int(state.get("global_count", 0) or 0),
        "watch": dict(state.get("watch", {}) or {}),
    }

    dom = str((context or {}).get("domain", ""))
    sub = str((context or {}).get("subdomain", ""))
    domain_tag = f"{dom}:{sub}" if (dom or sub) else "unknown:unknown"
    now = _iso_now_fallback(run_at_iso)

    # Ensure watch map exists and includes configured tokens
    if cfg.watchlist_tokens:
        wm = _build_watch_map(cfg.watchlist_tokens)
        # merge deterministically: existing last_variant_count preserved where keys overlap
        for k, v in wm.items():
            if k not in st["watch"]:
                st["watch"][k] = v

    an = (anagram_artifact or {}).get("shadow_anagram_v1") or {}
    cands = an.get("candidates", []) or []

    # Per-update counts to detect bursts
    per_key_incr: Dict[str, int] = {}

    for c in cands:
        src = str(c.get("src", "")).strip()
        dst = str(c.get("dst", "")).strip()
        if not src or not dst:
            continue

        src_norm = _norm_token_letters(src)
        dst_norm = _norm_token_letters(dst)
        if not src_norm or not dst_norm:
            continue

        # Cluster by the multiset key of the *source* (same as dst for true anagrams)
        key = _key_from_norm(src_norm)

        if key not in st["clusters"]:
            if len(st["clusters"]) >= budgets.max_clusters:
                # capacity reached: drop new keys deterministically
                continue
            st["clusters"][key] = {
                "key": key,
                "counts": 0,
                "first_seen": now,
                "last_seen": now,
                "src_tokens": [],
                "dst_variants": [],
                "domain_tags": [],
                "burst": False,
            }

        cl = st["clusters"][key]
        cl["counts"] = int(cl.get("counts", 0) or 0) + 1
        cl["last_seen"] = now
        _stable_add_unique(cl["src_tokens"], src, budgets.max_src_tokens_per_cluster)
        _stable_add_unique(cl["dst_variants"], dst, budgets.max_variants_per_cluster)
        _stable_add_unique(cl["domain_tags"], domain_tag, budgets.max_domain_tags_per_cluster)

        per_key_incr[key] = per_key_incr.get(key, 0) + 1
        st["global_count"] += 1

    # Burst marking: if any key increments above threshold in this update
    for key, inc in per_key_incr.items():
        if inc >= cfg.burst_delta:
            st["clusters"][key]["burst"] = True

    return st


def emit_cluster_artifact(
    state: Dict[str, Any],
    *,
    config: Optional[ClusterConfig] = None,
) -> Dict[str, Any]:
    """
    Emit a bounded, stable artifact suitable for Signal Layer shadow attachment.
    """
    cfg = config or ClusterConfig()
    budgets = cfg.budgets

    watch = dict(state.get("watch", {}) or {})

    clusters = list((state.get("clusters") or {}).values())
    # Stable sort by counts desc, then key asc
    clusters.sort(key=lambda c: (-int(c.get("counts", 0) or 0), str(c.get("key", ""))))
    clusters = clusters[: budgets.max_clusters]

    # Normalize each cluster with stable ordering for lists
    out_clusters = []
    for c in clusters:
        srcs = sorted(set(c.get("src_tokens") or []))[: budgets.max_src_tokens_per_cluster]
        dsts = sorted(set(c.get("dst_variants") or []))[: budgets.max_variants_per_cluster]
        dts = sorted(set(c.get("domain_tags") or []))[: budgets.max_domain_tags_per_cluster]
        out_clusters.append({
            "key": str(c.get("key", "")),
            "counts": int(c.get("counts", 0) or 0),
            "first_seen": str(c.get("first_seen", "")),
            "last_seen": str(c.get("last_seen", "")),
            "burst": bool(c.get("burst", False)),
            "src_tokens": srcs,
            "dst_variants": dsts,
            "domain_tags": dts,
        })

    # Watchlist alerts (deterministic)
    watchlist = []
    watch_alerts = []

    # stable order: by key asc
    for k in sorted(watch.keys()):
        w = watch[k]
        watchlist.append({"key": k, "token": str(w.get("token", ""))})

        # If cluster exists, compute variant delta since last emit
        cl = (state.get("clusters") or {}).get(k)
        if not isinstance(cl, dict):
            continue
        variants = sorted(set(cl.get("dst_variants") or []))
        variant_count = len(variants)
        last = int(w.get("last_variant_count", 0) or 0)
        delta = variant_count - last

        if delta > 0 or bool(cl.get("burst", False)):
            watch_alerts.append({
                "key": k,
                "token": str(w.get("token", "")),
                "counts": int(cl.get("counts", 0) or 0),
                "last_seen": str(cl.get("last_seen", "")),
                "burst": bool(cl.get("burst", False)),
                "variant_count": variant_count,
                "new_variants": max(0, delta),
                "variants_sample": variants[: min(5, len(variants))],
            })

        # Update last_variant_count in state (pure function expectation is on caller;
        # so we DO NOT mutate state here. Caller may persist updated state explicitly.)

    # Stable sort alerts: new_variants desc, counts desc, key asc
    watch_alerts.sort(key=lambda a: (-int(a.get("new_variants", 0) or 0), -int(a.get("counts", 0) or 0), str(a.get("key", ""))))
    watch_alerts = watch_alerts[: budgets.max_watch_alerts]

    artifact = {
        "shadow_anagram_cluster_v1": {
            "clusters": out_clusters,
            "global_count": int(state.get("global_count", 0) or 0),
            "watchlist": watchlist,
            "watch_alerts": watch_alerts,
            "not_computable": False,
        }
    }
    artifact_hash = sha256_hex(canonical_json(artifact))
    artifact["shadow_anagram_cluster_v1"]["artifact_hash"] = artifact_hash
    artifact["shadow_anagram_cluster_v1"]["provenance"] = {
        "module": "shadow_anagram_cluster_v1",
        "budgets": {
            "max_clusters": budgets.max_clusters,
            "max_variants_per_cluster": budgets.max_variants_per_cluster,
            "max_src_tokens_per_cluster": budgets.max_src_tokens_per_cluster,
            "max_domain_tags_per_cluster": budgets.max_domain_tags_per_cluster,
            "max_watch_alerts": budgets.max_watch_alerts,
        },
        "burst_delta": cfg.burst_delta,
        "watchlist_count": len(watchlist),
    }
    return artifact
