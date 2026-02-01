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
from .provenance import hash_items_for_run, sha256_hex, stable_json_dumps
from .runes.invoke import invoke_rune
from .sas import SASParams, compute_sas_for_sub
from .schema import ledger_entry, output_skeleton
from .sdct.registry import get_enabled_domains
from .tiering import apply_tier
from .types import PFDIAlert, SubAnagramHit


def load_items_jsonl(path: Path) -> List[dict]:
    items = read_jsonl(path)
    validate_items(items)
    return sort_items(items)


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


def _motif_text_from_id(motif_id: str) -> str:
    parts = motif_id.split(":", 2)
    if len(parts) == 3:
        return parts[2]
    return ""


def _aggregate_evidence(
    evidence: List[dict],
    sas_params: SASParams,
) -> List[dict]:
    stats: Dict[tuple[str, str], dict] = {}
    for ev in evidence:
        key = (ev.get("domain_id", ""), ev.get("motif_id", ""))
        rec = stats.setdefault(key, {
            "mentions_total": 0,
            "sources": set(),
            "events": set(),
            "tap_max": 0.0,
            "pfdi_max": 0.0,
        })
        rec["mentions_total"] += int(ev.get("mentions", 0))
        rec["sources"].add(ev.get("source", ""))
        rec["events"].add(ev.get("event_key", ""))
        signals = ev.get("signals", {})
        rec["tap_max"] = max(rec["tap_max"], float(signals.get("tap", 0.0)))
        rec["pfdi_max"] = max(rec["pfdi_max"], float(signals.get("pfdi", 0.0)))

    rows: List[dict] = []
    for (domain_id, motif_id), rec in sorted(stats.items(), key=lambda x: (x[0][0], x[0][1])):
        motif_text = _motif_text_from_id(motif_id)
        motif_len = len(motif_text) if motif_text else 0
        sas = compute_sas_for_sub(
            mentions=rec["mentions_total"],
            sources_count=len(rec["sources"]),
            events_count=len(rec["events"]),
            sub_len=motif_len,
            params=sas_params,
        )
        row = {
            "domain_id": domain_id,
            "motif_id": motif_id,
            "motif_text": motif_text,
            "motif_len": motif_len,
            "sas": sas,
            "mentions": rec["mentions_total"],
            "sources_count": len(rec["sources"]),
            "events_count": len(rec["events"]),
            "lane": "",
            "tap_max": rec["tap_max"],
            "pfdi_max": rec["pfdi_max"],
        }
        if domain_id == "sdct.text_subword.v1":
            row["sub"] = motif_text
        rows.append(row)
    return rows


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

    canary_words = set()
    if lanes_dir is not None:
        canary_words = set(load_canary_words(lanes_dir))

    registry = get_enabled_domains()
    registry = sorted(registry, key=lambda r: (r.rune_id, r.domain_id))
    domain_ids = [entry.domain_id for entry in registry]

    collisions: List[dict] = []
    rt = build_runtime_lexicon(core_subwords=lex.subwords, canary_subwords=frozenset(canary_words))
    subs: List[SubAnagramHit] = []
    hightap: List[dict] = []
    token_records_count = 0

    # deterministic cluster key per item_id for downstream diversity accounting
    id_to_cluster = {str(it.get("id", "")): _cluster_key(it, key) for it in items_sorted}
    id_to_keyed = {
        str(it.get("id", "")): keyed_id(key, f"item|{it.get('id', '')}", n=16)
        for it in items_sorted
    } if key else {}

    evidence: List[dict] = []
    evidence_counts_by_domain: Dict[str, int] = defaultdict(int)

    event_keys = {str(k): v for k, v in id_to_cluster.items()}
    ctx = {
        "run_id": run_id,
        "date": date,
        "key_fingerprint": key_fp,
        "schema_versions": {"sdct": "v0.1"},
        "runtime_lexicon_hash": rt.runtime_hash,
    }

    sdct_domains: List[dict] = []
    sdct_evidence_rows: List[dict] = []
    sdct_motif_stats_by_domain: Dict[str, List[dict]] = {}
    digit_motifs_by_item_id: Dict[str, List[str]] = {}

    for entry in registry:
        domain_id = entry.domain_id
        rune_id = entry.rune_id
        payload = {
            "items": items_sorted,
            "date": date,
            "event_keys_by_item_id": event_keys,
        }
        if digit_motifs_by_item_id:
            payload["digit_motifs_by_item_id"] = digit_motifs_by_item_id
        result = invoke_rune(rune_id, payload, ctx)
        if result.get("status") != "ok":
            raise RuntimeError(f"Rune invocation failed: {rune_id} ({result.get('errors')})")

        sdct_domains.append({
            "descriptor": result.get("descriptor", {}),
            "provenance": result.get("provenance", {}),
        })

        evidence_rows = result.get("evidence_rows", [])
        evidence.extend(evidence_rows)
        evidence_counts_by_domain[domain_id] += len(evidence_rows)
        sdct_evidence_rows.extend(evidence_rows)
        sdct_motif_stats_by_domain[domain_id] = result.get("motif_stats", [])

        if domain_id == "sdct.digit_motif.v1":
            digit_motifs_by_item_id = {}
            for row in evidence_rows:
                if row.get("domain_id") != "sdct.digit_motif.v1":
                    continue
                motif_id = str(row.get("motif_id", ""))
                digits = motif_id.split(":", 1)[1] if ":" in motif_id else motif_id
                item_id = str(row.get("item_id", ""))
                digit_motifs_by_item_id.setdefault(item_id, []).append(digits)
            for item_id in digit_motifs_by_item_id:
                digit_motifs_by_item_id[item_id] = sorted(set(digit_motifs_by_item_id[item_id]))

        if domain_id == "sdct.text_subword.v1":
            legacy = result.get("legacy", {})
            collisions = legacy.get("exact_collisions", [])
            hightap = legacy.get("high_tap_tokens", [])
            token_records_count = int(legacy.get("token_records", 0))
            subs = [SubAnagramHit(**h) for h in legacy.get("verified_sub_anagrams", [])]

    # load pfdi state
    if pfdi_state_path and pfdi_state_path.exists():
        pfdi_state = json.loads(pfdi_state_path.read_text(encoding="utf-8"))
    else:
        pfdi_state = {"version": 1, "stats": {}}

    alerts, new_state, ledger_rows = compute_pfdi(items_sorted, subs, pfdi_state, key)

    report = output_skeleton(date=date, run_id=run_id, items_hash=items_hash, version=__version__)
    report["sdct"] = {
        "domains": sdct_domains,
        "evidence_rows": sdct_evidence_rows,
        "motif_stats_by_domain": sdct_motif_stats_by_domain,
    }
    report["domains"] = sdct_domains
    report["evidence_counts_by_domain"] = {
        domain_id: int(evidence_counts_by_domain.get(domain_id, 0))
        for domain_id in sorted(domain_ids)
    }
    report["exact_collisions"] = collisions
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
    report["schema_versions"] = {"ase_output": "v0.1", "sdct": "v0.1"}
    if key_fp:
        report["key_fingerprint"] = key_fp
    if enterprise_diagnostics:
        report["enterprise_diagnostics"] = enterprise_diagnostics

    sas_params = SASParams()
    sas_rows = _aggregate_evidence(evidence, sas_params)

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
        "token_records": token_records_count,
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
