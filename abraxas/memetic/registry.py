from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from abraxas.evolve.ledger import append_chained_jsonl


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def term_key(term: str) -> str:
    h = hashlib.sha256(term.strip().lower().encode("utf-8")).hexdigest()
    return h[:16]


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _read_jsonl(path: str, max_lines: int = 200000) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    out: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
    return out


def load_known_term_keys(registry_path: str) -> Dict[str, Dict[str, Any]]:
    rows = _read_jsonl(registry_path)
    latest: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        key = row.get("term_key")
        if not key:
            continue
        latest[str(key)] = row
    return latest


def append_a2_terms_to_registry(
    *,
    a2_path: str,
    registry_path: str = "out/a2_registry/terms.jsonl",
    source_run_id: Optional[str] = None,
) -> Dict[str, Any]:
    a2 = _read_json(a2_path)
    macro_risk = 0.0
    try:
        macro_risk = float(((a2.get("dmx") or {}).get("overall_manipulation_risk")) or 0.0)
    except Exception:
        macro_risk = 0.0
    ts = str(a2.get("ts") or _utc_now_iso())
    run_id = source_run_id or str(a2.get("run_id") or "unknown")
    terms = a2.get("terms") or []
    if not isinstance(terms, list):
        terms = []

    appended = 0
    for term in terms:
        if not isinstance(term, dict):
            continue
        text = str(term.get("term") or "").strip()
        if not text:
            continue
        key = term_key(text)
        rec = {
            "version": "a2_registry_row.v0.1",
            "ts": ts,
            "source_run_id": run_id,
            "term_key": key,
            "term": text,
            "term_id": str(term.get("term_id") or ""),
            "n": int(term.get("n") or (1 + text.count(" "))),
            "count": int(term.get("count") or 0),
            "first_seen_ts": str(term.get("first_seen_ts") or ts),
            "last_seen_ts": str(term.get("last_seen_ts") or ts),
            "velocity_per_day": float(term.get("velocity_per_day") or 0.0),
            "half_life_est_s": float(term.get("half_life_est_s") or 0.0),
            "novelty_score": float(term.get("novelty_score") or 0.0),
            "propagation_score": float(term.get("propagation_score") or 0.0),
            "manipulation_risk": float(
                0.70 * float(term.get("manipulation_risk") or 0.0) + 0.30 * macro_risk
            ),
            "tags": list(term.get("tags") or []),
            "provenance": {
                "method": "append_a2_terms_to_registry.v0.1",
                "a2_path": a2_path,
            },
        }
        append_chained_jsonl(registry_path, rec)
        appended += 1

    return {
        "appended": appended,
        "registry_path": registry_path,
        "source_run_id": run_id,
    }


def compute_missed_terms(
    *,
    a2_path: str,
    registry_path: str = "out/a2_registry/terms.jsonl",
    resurrect_after_days: int = 10,
) -> Dict[str, Any]:
    a2 = _read_json(a2_path)
    ts = str(a2.get("ts") or _utc_now_iso())
    terms = a2.get("terms") or []
    if not isinstance(terms, list):
        terms = []

    known = load_known_term_keys(registry_path)

    missed: List[Dict[str, Any]] = []
    resurrected: List[Dict[str, Any]] = []
    present_keys: List[str] = []

    def _parse_dt(s: str) -> Optional[datetime]:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    now_dt = _parse_dt(ts) or datetime.now(timezone.utc)
    threshold_s = float(resurrect_after_days) * 86400.0

    for term in terms:
        if not isinstance(term, dict):
            continue
        text = str(term.get("term") or "").strip()
        if not text:
            continue
        key = term_key(text)
        present_keys.append(key)
        prev = known.get(key)
        if prev is None:
            missed.append(term)
            continue
        prev_last = _parse_dt(str(prev.get("last_seen_ts") or prev.get("ts") or ""))
        if prev_last is None:
            continue
        age_s = (now_dt - prev_last).total_seconds()
        if age_s >= threshold_s:
            resurrected.append(term)

    def _rank(x: Dict[str, Any]) -> tuple[float, str]:
        novelty = float(x.get("novelty_score") or 0.0)
        prop = float(x.get("propagation_score") or 0.0)
        score = novelty + prop
        return (-score, str(x.get("term") or ""))

    missed.sort(key=_rank)
    resurrected.sort(key=_rank)

    return {
        "version": "a2_missed.v0.1",
        "ts": ts,
        "run_id": str(a2.get("run_id") or "unknown"),
        "a2_path": a2_path,
        "registry_path": registry_path,
        "present": len(set(present_keys)),
        "known": len(known),
        "missed": missed,
        "resurrected": resurrected,
        "params": {"resurrect_after_days": resurrect_after_days},
        "provenance": {"method": "compute_missed_terms.v0.1"},
    }
