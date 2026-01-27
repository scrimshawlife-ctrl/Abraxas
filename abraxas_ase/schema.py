from __future__ import annotations

from .types import JsonDict


def output_skeleton(date: str, run_id: str, items_hash: str, version: str) -> JsonDict:
    return {
        "date": date,
        "version": version,
        "run_id": run_id,
        "items_hash": items_hash,
        "domains": [],
        "evidence_counts_by_domain": {},
        "exact_collisions": [],
        "high_tap_tokens": [],
        "verified_sub_anagrams": [],
        "pfdi_alerts": [],
        "stats": {},
    }


def ledger_entry(
    date: str,
    run_id: str,
    items_hash: str,
    key: str,
    sub: str,
    mentions: int,
    mean: float,
    std: float,
    pfdi: float,
) -> JsonDict:
    return {
        "date": date,
        "run_id": run_id,
        "items_hash": items_hash,
        "key": key,
        "sub": sub,
        "mentions_today": mentions,
        "baseline_mean": mean,
        "baseline_std": std,
        "pfdi": pfdi,
    }
