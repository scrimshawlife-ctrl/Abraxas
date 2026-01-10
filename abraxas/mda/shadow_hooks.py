from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from abraxas.detectors.shadow.anagram import detect_shadow_anagrams
from abraxas.detectors.shadow.anagram_cluster import (
    init_cluster_state,
    update_anagram_clusters,
    emit_cluster_artifact,
    ClusterConfig,
)


def _load_json(path: str) -> Optional[Dict[str, Any]]:
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, obj: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)


def _extract_tokens_from_payload(payload: Dict[str, Any], *, cap: int = 200) -> List[str]:
    """
    Deterministic token extraction for shadow anagram detector.
    This is intentionally simple: pull obvious string fields and tag-like atoms.
    """
    out: List[str] = []

    def add(s: Any) -> None:
        if not isinstance(s, str):
            return
        s2 = s.strip()
        if not s2:
            return
        out.append(s2)

    def walk(x: Any) -> None:
        if len(out) >= cap:
            return
        if isinstance(x, dict):
            for k in sorted(x.keys()):
                v = x[k]
                if k in ("title", "name", "handle", "hashtag", "tag", "tags", "actor", "actors", "meme", "memes"):
                    add(v)
                walk(v)
                if len(out) >= cap:
                    return
        elif isinstance(x, list):
            for it in x:
                walk(it)
                if len(out) >= cap:
                    return
        else:
            add(x)

    walk(payload)
    out2 = sorted(set(out))
    return out2[:cap]


def _extract_evidence_refs(payload: Dict[str, Any], *, cap: int = 50) -> List[str]:
    """
    Pull any evidence_refs arrays if present; deterministic union.
    """
    refs: List[str] = []

    def add_ref(x: Any) -> None:
        if isinstance(x, str) and x.strip():
            refs.append(x.strip())

    def walk(x: Any) -> None:
        if len(refs) >= cap:
            return
        if isinstance(x, dict):
            for k in sorted(x.keys()):
                v = x[k]
                if k == "evidence_refs" and isinstance(v, list):
                    for it in v:
                        add_ref(it)
                walk(v)
                if len(refs) >= cap:
                    return
        elif isinstance(x, list):
            for it in x:
                walk(it)
                if len(refs) >= cap:
                    return

    walk(payload)
    return sorted(set(refs))[:cap]


def apply_shadow_anagram_detectors(
    *,
    mda_out: Dict[str, Any],
    payload: Optional[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
    run_at_iso: str,
    out_dir: str,
    watchlist_tokens: Tuple[str, ...] = (),
) -> Dict[str, Any]:
    """
    Additive shadow hook:
      - detect_shadow_anagrams(tokens)
      - update cluster state (persisted under out_dir/shadow_state/)
      - attach under mda_out["shadow"]
    Deterministic if payload/run_at_iso fixed.
    """
    if payload is None:
        shadow = dict(mda_out.get("shadow", {}) or {})
        shadow["anagram_v1"] = {"shadow_anagram_v1": {"candidates": [], "not_computable": True}}
        shadow["anagram_cluster_v1"] = {"shadow_anagram_cluster_v1": {"clusters": [], "not_computable": True}}
        mda_out["shadow"] = shadow
        return mda_out

    tokens = _extract_tokens_from_payload(payload)
    ev_refs = _extract_evidence_refs(payload)

    an_art = detect_shadow_anagrams(
        tokens,
        context=context,
        evidence_refs=ev_refs if ev_refs else None,
    )

    state_dir = os.path.join(out_dir, "shadow_state")
    state_path = os.path.join(state_dir, "anagram_cluster_state.json")
    st = _load_json(state_path) or init_cluster_state()

    cfg = ClusterConfig(watchlist_tokens=watchlist_tokens)
    st2 = update_anagram_clusters(
        st,
        anagram_artifact=an_art,
        context=context,
        run_at_iso=run_at_iso,
        config=cfg,
    )
    cl_art = emit_cluster_artifact(st2, config=cfg)

    watch_alerts = (cl_art.get("shadow_anagram_cluster_v1") or {}).get("watch_alerts") or []
    for a in watch_alerts:
        key = str(a.get("key", ""))
        if not key:
            continue
        if "watch" not in st2:
            st2["watch"] = {}
        if key not in st2["watch"]:
            st2["watch"][key] = {"token": str(a.get("token", "")), "last_variant_count": 0}
        st2["watch"][key]["last_variant_count"] = int(a.get("variant_count", 0) or 0)

    _write_json(state_path, st2)

    shadow = dict(mda_out.get("shadow", {}) or {})
    shadow["anagram_v1"] = an_art
    shadow["anagram_cluster_v1"] = cl_art
    mda_out["shadow"] = shadow
    return mda_out
