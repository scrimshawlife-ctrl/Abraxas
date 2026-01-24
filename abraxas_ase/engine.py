from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import __version__
from .lexicon import Lexicon, build_default_lexicon
from .lexicon_runtime import build_runtime_lexicon, load_canary_words
from .io import read_jsonl, sort_items, validate_items
from .keyed import key_fingerprint, keyed_id, read_key_or_none, require_key
from .normalize import extract_tokens, filter_token, is_stopish, normalize_token, split_hyphenated
from .provenance import hash_items_for_run, make_run_id, sha256_hex, stable_json_dumps
from .sas import SASParams, compute_sas_for_sub
from .scoring import letter_entropy, stable_round, token_anagram_potential
from .schema import ledger_entry, output_skeleton
from .tiering import apply_tier
from .types import ExactCollision, PFDIAlert, SubAnagramHit, TokenRec


def _letters_sorted(tok: str) -> str:
    # tok already normalized; strip hyphen/apostrophe for letter pool
    bare = tok.replace("-", "").replace("'", "")
    return "".join(sorted(bare))


def _can_spell(parent_letters: Counter, sub: str) -> bool:
    need = Counter(sub)
    for ch, n in need.items():
        if parent_letters.get(ch, 0) < n:
            return False
    return True


def load_items_jsonl(path: Path) -> List[dict]:
    items = read_jsonl(path)
    validate_items(items)
    return sort_items(items)


def build_token_records(items: List[dict], lex: Lexicon, min_len: int = 4) -> List[TokenRec]:
    out: List[TokenRec] = []
    for it in items:
        item_id = str(it.get("id", ""))
        source = str(it.get("source", ""))
        # deterministic text concatenation order
        blob = f"{it.get('title', '')}\n{it.get('text', '')}"
        raw_tokens = extract_tokens(blob)
        for raw in raw_tokens:
            nt = normalize_token(raw)
            if not nt:
                continue
            if is_stopish(nt, set(lex.stopwords)):
                continue
            # keep joined hyphenated token
            cand = [nt]
            # and also split parts (adds recall; deterministic)
            if "-" in nt:
                cand.extend(split_hyphenated(nt))
            for t in cand:
                if not filter_token(t, min_len=min_len):
                    continue
                ls = _letters_sorted(t)
                if not ls:
                    continue
                ent = letter_entropy(ls)
                ul = len(set(ls))
                tap = token_anagram_potential(len(ls), ul)
                out.append(TokenRec(
                    token=t,
                    norm=t,
                    letters_sorted=ls,
                    length=len(ls),
                    unique_letters=ul,
                    letter_entropy=float(ent),
                    tap=float(tap),
                    item_id=item_id,
                    source=source,
                ))
    # deterministic ordering (by letters then token then item)
    return sorted(out, key=lambda r: (r.letters_sorted, r.norm, r.source, r.item_id))


def tier1_exact_collisions(recs: List[TokenRec], min_sources: int = 2) -> List[ExactCollision]:
    bucket: Dict[str, List[TokenRec]] = defaultdict(list)
    for r in recs:
        bucket[r.letters_sorted].append(r)

    collisions: List[ExactCollision] = []
    for k, rs in bucket.items():
        toks = sorted({x.norm for x in rs})
        if len(toks) < 2:
            continue
        sources = sorted({x.source for x in rs})
        if len(sources) < min_sources:
            continue
        ids = sorted({x.item_id for x in rs})
        collisions.append(ExactCollision(letters_sorted=k, tokens=toks, sources=sources, item_ids=ids))

    # deterministic
    return sorted(collisions, key=lambda c: (c.letters_sorted, c.tokens))


def tier2_subanagrams(
    recs: List[TokenRec],
    lex: Lexicon,
    min_sub_len: int = 3,
    canary_subwords: Optional[set[str]] = None,
) -> List[SubAnagramHit]:
    core = sorted([w for w in lex.subwords if len(w) >= min_sub_len])
    canary = sorted([w for w in (canary_subwords or set()) if len(w) >= min_sub_len and w not in lex.subwords])
    subs_all = core + canary
    hits: List[SubAnagramHit] = []
    for r in recs:
        parent = Counter(r.letters_sorted)
        for sub in subs_all:
            if _can_spell(parent, sub):
                lane = "core" if sub in lex.subwords else "canary"
                hits.append(SubAnagramHit(
                    token=r.norm,
                    sub=sub,
                    tier=2,
                    verified=True,
                    lane=lane,
                    item_id=r.item_id,
                    source=r.source,
                ))
    # deterministically unique by (token, sub, item_id)
    uniq = {}
    for h in hits:
        key = (h.token, h.sub, h.lane, h.item_id, h.source)
        uniq[key] = h
    out = list(uniq.values())
    return sorted(out, key=lambda h: (h.sub, h.token, h.source, h.item_id))


def high_tap_tokens(recs: List[TokenRec], top_k: int = 25, per_token_max: int = 1) -> List[dict]:
    # aggregate by token, take max tap
    best: Dict[str, TokenRec] = {}
    for r in recs:
        prev = best.get(r.norm)
        if prev is None or r.tap > prev.tap:
            best[r.norm] = r
    ranked = sorted(best.values(), key=lambda r: (-r.tap, -r.letter_entropy, r.norm))
    ranked = ranked[:top_k]
    out: List[dict] = []
    for r in ranked:
        out.append({
            "token": r.norm,
            "tap": stable_round(r.tap),
            "letter_entropy": stable_round(r.letter_entropy),
            "length": r.length,
            "unique_letters": r.unique_letters,
        })
    return out


def _cluster_key(it: dict, key: bytes | None) -> str:
    """
    Deterministic phrase-field key.
    We avoid topic modeling (non-deterministic / corpus-dependent).
    Key = source + first 64 chars of normalized title.
    """
    title = str(it.get("title", "")).strip().lower()
    title = "".join(ch for ch in title if ch.isalnum() or ch.isspace())
    title = " ".join(title.split())
    raw = f"cluster|{it.get('source', '')}|{title[:64]}"
    if key:
        return keyed_id(key, raw, n=32)
    return sha256_hex(raw.encode("utf-8"))


def compute_pfdi(
    items: List[dict],
    tier2_hits: List[SubAnagramHit],
    pfdi_state: dict,
    key: bytes | None,
) -> Tuple[List[PFDIAlert], dict, List[dict]]:
    """
    PFDI baseline:
      For each (cluster_key, sub), keep Welford running mean/var.
    Today mentions = count of tier2 hits whose item maps to cluster_key.
    """
    # map item_id->cluster_key deterministically
    id_to_key: Dict[str, str] = {}
    for it in items:
        id_to_key[str(it.get("id", ""))] = _cluster_key(it, key)

    # today counts
    today = Counter()
    for h in tier2_hits:
        key = id_to_key.get(h.item_id)
        if key is None:
            continue
        today[(key, h.sub)] += 1

    # update state
    state = pfdi_state or {"version": 1, "stats": {}}  # stats[(key|sub)] => {n, mean, m2}
    stats = state.get("stats", {})
    alerts: List[PFDIAlert] = []
    ledger_rows: List[dict] = []

    # thresholds (deterministic constants)
    PF_DI_THRESHOLD = 3.0
    MIN_N_FOR_STD = 7  # baseline stability

    for (key, sub), mentions in sorted(today.items(), key=lambda x: (x[0][0], x[0][1])):
        sk = f"{key}||{sub}"
        rec = stats.get(sk, {"n": 0, "mean": 0.0, "m2": 0.0})
        n = int(rec["n"])
        mean = float(rec["mean"])
        m2 = float(rec["m2"])

        # compute pfdi using current baseline BEFORE updating (so today's spike compares to prior history)
        if n >= MIN_N_FOR_STD:
            var = m2 / (n - 1) if n > 1 else 0.0
            std = math.sqrt(var) if var > 0 else 0.0
            pfdi = (mentions - mean) / std if std > 0 else 0.0
        else:
            std = 0.0
            pfdi = 0.0

        if n >= MIN_N_FOR_STD and pfdi >= PF_DI_THRESHOLD:
            alerts.append(PFDIAlert(
                key=key,
                sub=sub,
                pfdi=float(pfdi),
                mentions_today=int(mentions),
                baseline_mean=float(mean),
                baseline_std=float(std),
            ))

        # update baseline with today's mentions (Welford)
        n2 = n + 1
        delta = mentions - mean
        mean2 = mean + delta / n2
        delta2 = mentions - mean2
        m2_2 = m2 + delta * delta2

        stats[sk] = {"n": n2, "mean": float(mean2), "m2": float(m2_2)}

        ledger_rows.append({
            "key": key,
            "sub": sub,
            "mentions_today": int(mentions),
            "baseline_mean": float(mean),
            "baseline_std": float(std),
            "pfdi": float(pfdi),
        })

    # deterministic ordering
    alerts = sorted(alerts, key=lambda a: (-a.pfdi, a.key, a.sub))
    state["stats"] = stats
    return alerts, state, ledger_rows


def run_ase(
    items: List[dict],
    date: str,
    outdir: Path,
    pfdi_state_path: Optional[Path] = None,
    lanes_dir: Optional[Path] = None,
    lex: Optional[Lexicon] = None,
    tier: str = "academic",
    safe_export: bool = True,
    include_urls: bool = False,
    enterprise_diagnostics: Optional[dict] = None,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    lex = lex or build_default_lexicon()

    tier_norm = (tier or "psychonaut").lower()
    key = read_key_or_none()
    if tier_norm in {"academic", "enterprise"}:
        key = require_key()
    key_fp = key_fingerprint(key) if key else None

    items_sorted = sort_items(items)
    items_hash = hash_items_for_run(items_sorted)
    run_id = keyed_id(key, f"run|{date}|{items_hash}", n=16) if key else None

    recs = build_token_records(items_sorted, lex=lex, min_len=4)
    collisions = tier1_exact_collisions(recs)
    canary_words = set()
    if lanes_dir is not None:
        canary_words = set(load_canary_words(lanes_dir))

    rt = build_runtime_lexicon(core_subwords=lex.subwords, canary_subwords=frozenset(canary_words))
    subs = tier2_subanagrams(recs, lex=lex, min_sub_len=3, canary_subwords=canary_words)
    hightap = high_tap_tokens(recs, top_k=30)

    # deterministic cluster key per item_id for downstream diversity accounting
    id_to_cluster = {str(it.get("id", "")): _cluster_key(it, key) for it in items_sorted}
    id_to_keyed = {
        str(it.get("id", "")): keyed_id(key, f"item|{it.get('id', '')}", n=16)
        for it in items_sorted
    } if key else {}

    # load pfdi state
    if pfdi_state_path and pfdi_state_path.exists():
        pfdi_state = json.loads(pfdi_state_path.read_text(encoding="utf-8"))
    else:
        pfdi_state = {"version": 1, "stats": {}}

    alerts, new_state, ledger_rows = compute_pfdi(items_sorted, subs, pfdi_state, key)

    report = output_skeleton(date=date, run_id=run_id, items_hash=items_hash, version=__version__)
    report["exact_collisions"] = [asdict(c) for c in collisions]
    report["high_tap_tokens"] = hightap
    report["verified_sub_anagrams"] = [
        {
            **asdict(h),
            "item_id": id_to_keyed.get(h.item_id, h.item_id),
        }
        for h in subs
    ]
    report["pfdi_alerts"] = [asdict(a) for a in alerts]
    report["clusters"] = {
        "by_item_id": {id_to_keyed.get(k, k): v for k, v in id_to_cluster.items()},
        "cluster_key_version": 1,
    }
    report["runtime_lexicon"] = {"runtime_hash": rt.runtime_hash, "canary_count": len(canary_words)}
    report["schema_versions"] = {"ase_output": "v0.1"}
    if key_fp:
        report["key_fingerprint"] = key_fp
    if enterprise_diagnostics:
        report["enterprise_diagnostics"] = enterprise_diagnostics

    # SAS per subword (core+canary) based on today's evidence
    sas_params = SASParams()
    sub_mentions = Counter()
    sub_sources = defaultdict(set)
    sub_events = defaultdict(set)

    for h in subs:
        sub_mentions[h.sub] += 1
        sub_sources[h.sub].add(h.source)
        sub_events[h.sub].add(id_to_cluster.get(h.item_id, f"item:{h.item_id}"))

    sas_rows = []
    for sub, m in sorted(sub_mentions.items(), key=lambda x: x[0]):
        sc = compute_sas_for_sub(
            mentions=m,
            sources_count=len(sub_sources[sub]),
            events_count=len(sub_events[sub]),
            sub_len=len(sub),
            params=sas_params,
        )
        sas_rows.append({
            "sub": sub,
            "sas": sc,
            "mentions": m,
            "sources_count": len(sub_sources[sub]),
            "events_count": len(sub_events[sub]),
            "lane": "core" if sub in lex.subwords else "canary",
        })

    report["sas"] = {
        "params": {
            "w_count": sas_params.w_count,
            "w_sources": sas_params.w_sources,
            "w_events": sas_params.w_events,
            "w_len": sas_params.w_len,
            "max_len_bonus": sas_params.max_len_bonus,
        },
        "rows": sas_rows,
    }
    report["stats"] = {
        "items": len(items_sorted),
        "token_records": len(recs),
        "tier1_collisions": len(collisions),
        "tier2_hits": len(subs),
        "pfdi_alerts": len(alerts),
    }

    report = apply_tier(report, tier=tier_norm, safe_export=safe_export, include_urls=include_urls)
    (outdir / "daily_report.json").write_text(stable_json_dumps(report), encoding="utf-8")
    (outdir / "pfdi_state.json").write_text(stable_json_dumps(new_state), encoding="utf-8")

    # append ledger jsonl (deterministic ordering already)
    ledger_path = outdir / "ledger_append.jsonl"
    with ledger_path.open("w", encoding="utf-8") as f:
        for row in ledger_rows:
            entry = ledger_entry(
                date=date,
                run_id=run_id,
                items_hash=items_hash,
                key=row["key"],
                sub=row["sub"],
                mentions=row["mentions_today"],
                mean=row["baseline_mean"],
                std=row["baseline_std"],
                pfdi=row["pfdi"],
            )
            f.write(stable_json_dumps(entry) + "\n")
