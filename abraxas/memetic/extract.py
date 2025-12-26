from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .types import MimeticWeatherUnit, TermCandidate


TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']{1,48}")

DISINFO_MARKERS = [
    "deepfake",
    "ai generated",
    "synthetic",
    "fabricated",
    "hoax",
    "psyop",
    "false flag",
    "propaganda",
    "misinformation",
    "disinformation",
    "leaked video",
    "doctored",
]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _tokenize(text: str) -> List[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text or "")]


def _ngrams(tokens: List[str], n: int) -> List[str]:
    if n <= 1:
        return tokens
    return [" ".join(tokens[i : i + n]) for i in range(0, max(0, len(tokens) - n + 1))]


def _parse_ts(s: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _days_between(a: str, b: str) -> float:
    da = _parse_ts(a)
    db = _parse_ts(b)
    if not da or not db:
        return 1.0
    d = (db - da).total_seconds() / 86400.0
    return max(0.5, d)


def _half_life_est_s(first_ts: str, last_ts: str, count: int) -> float:
    days = _days_between(first_ts, last_ts)
    rate = count / days
    x = max(0.01, rate)
    hl_days = max(0.083, min(45.0, 3.5 / math.log10(10.0 + x)))
    return float(hl_days * 86400.0)


def _horizon_tags(half_life_s: float) -> List[str]:
    if half_life_s <= 12 * 3600:
        return ["intra_day"]
    if half_life_s <= 3 * 86400:
        return ["short_week"]
    if half_life_s <= 14 * 86400:
        return ["mid_month"]
    return ["long_tail"]


def _manipulation_risk(text: str, term: str) -> float:
    t = (text or "").lower()
    hits = sum(1 for marker in DISINFO_MARKERS if marker in t)
    adj = 0
    if any(k in t for k in ["footage", "video", "leak", "leaked", "recording"]):
        if term.lower() in t:
            adj = 1
    caps = sum(1 for w in re.findall(r"\b[A-Z]{3,}\b", text or ""))
    r = 0.08 * hits + 0.12 * adj + 0.02 * min(5, caps)
    return max(0.0, min(1.0, r))


def _novelty_score(term_count: int, baseline_count: int) -> float:
    if baseline_count <= 0:
        return 0.7
    ratio = term_count / max(1, baseline_count)
    return max(0.0, min(1.0, math.log10(1.0 + ratio) / 2.0))


def _propagation_score(count: int, velocity_per_day: float) -> float:
    c = max(0.0, min(1.0, math.log10(1.0 + count) / 4.0))
    v = max(0.0, min(1.0, math.log10(1.0 + velocity_per_day) / 2.5))
    return float(0.55 * c + 0.45 * v)


def read_oracle_texts(path: str, max_items: int = 200) -> List[Tuple[str, str]]:
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        raw_strip = raw.strip()
        if raw_strip.startswith("["):
            arr = json.loads(raw_strip)
            out: List[Tuple[str, str]] = []
            if isinstance(arr, list):
                for it in arr[:max_items]:
                    if not isinstance(it, dict):
                        continue
                    ts = str(it.get("ts") or it.get("timestamp") or it.get("date") or _utc_now_iso())
                    txt = it.get("text") or it.get("oracle") or it.get("content") or it.get("md") or ""
                    out.append((ts, str(txt)))
            return out
        if "\n" in raw and raw_strip.startswith("{"):
            out = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    it = json.loads(line)
                except Exception:
                    continue
                if not isinstance(it, dict):
                    continue
                ts = str(it.get("ts") or it.get("timestamp") or it.get("date") or _utc_now_iso())
                txt = it.get("text") or it.get("oracle") or it.get("content") or it.get("md") or ""
                out.append((ts, str(txt)))
                if len(out) >= max_items:
                    break
            return out
    except Exception:
        pass

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        blob = f.read()
    return [(_utc_now_iso(), blob)]


def extract_terms(
    docs: List[Tuple[str, str]],
    n_values: List[int] | None = None,
    max_terms: int = 60,
    baseline_counts: Optional[Dict[str, int]] = None,
) -> List[TermCandidate]:
    baseline_counts = baseline_counts or {}
    n_values = n_values or [1, 2, 3]
    counts: Counter[str] = Counter()
    first_seen: Dict[str, str] = {}
    last_seen: Dict[str, str] = {}
    sample_text: Dict[str, str] = {}

    for ts, text in docs:
        toks = _tokenize(text)
        for n in n_values:
            for ng in _ngrams(toks, n):
                if len(ng) <= 2:
                    continue
                counts[ng] += 1
                if ng not in first_seen:
                    first_seen[ng] = ts
                    sample_text[ng] = text[:1200]
                last_seen[ng] = ts

    top = counts.most_common(max_terms * 3)

    out: List[TermCandidate] = []
    for term, count in top:
        if term.isdigit():
            continue
        if term.count(" ") >= 4:
            continue

        fs = first_seen.get(term, docs[0][0] if docs else _utc_now_iso())
        ls = last_seen.get(term, fs)
        days = _days_between(fs, ls)
        vel = float(count / days)
        hl = _half_life_est_s(fs, ls, count)
        novelty = _novelty_score(count, int(baseline_counts.get(term, 0)))
        prop = _propagation_score(count, vel)
        risk = _manipulation_risk(sample_text.get(term, ""), term)
        tags = []
        tags.extend(_horizon_tags(hl))
        if novelty >= 0.65:
            tags.append("novel")
        if prop >= 0.55:
            tags.append("spreading")
        if risk >= 0.35:
            tags.append("manipulation_risk")

        term_id = _sha(f"{term}:{fs}:{ls}")[:16]
        out.append(
            TermCandidate(
                term_id=term_id,
                term=term,
                n=1 + term.count(" "),
                count=int(count),
                first_seen_ts=str(fs),
                last_seen_ts=str(ls),
                velocity_per_day=float(vel),
                half_life_est_s=float(hl),
                novelty_score=float(novelty),
                propagation_score=float(prop),
                manipulation_risk=float(risk),
                tags=sorted(list(set(tags))),
                provenance={"method": "extract_terms.v0.1", "baseline": "inline_counts"},
            )
        )

    def score(tc: TermCandidate) -> float:
        return (0.48 * tc.novelty_score + 0.52 * tc.propagation_score) - (
            0.25 * tc.manipulation_risk
        )

    out.sort(key=lambda tc: (-score(tc), -tc.count, tc.term))
    return out[:max_terms]


def build_mimetic_weather(
    run_id: str,
    terms: List[TermCandidate],
    ts: Optional[str] = None,
) -> List[MimeticWeatherUnit]:
    ts = ts or _utc_now_iso()

    fronts: Dict[str, List[TermCandidate]] = defaultdict(list)
    for term in terms:
        if "manipulation_risk" in term.tags:
            fronts["disinfo_fog"].append(term)
        if "novel" in term.tags and "spreading" in term.tags:
            fronts["novelty_front"].append(term)
        if "long_tail" in term.tags:
            fronts["long_tail_pressure"].append(term)
        if "intra_day" in term.tags:
            fronts["flash_spike"].append(term)

    units: List[MimeticWeatherUnit] = []
    for label, bucket in sorted(fronts.items(), key=lambda kv: kv[0]):
        if not bucket:
            continue
        inten = sum(
            (t.propagation_score * 0.65 + t.novelty_score * 0.35) for t in bucket
        ) / max(1, len(bucket))
        risk = sum(t.manipulation_risk for t in bucket) / max(1, len(bucket))
        conf = max(0.25, min(0.9, 0.55 + 0.25 * (1.0 - risk)))
        direction = (
            "rising"
            if sum(t.velocity_per_day for t in bucket) / max(1, len(bucket)) > 2.0
            else "steady"
        )
        fs = min((t.first_seen_ts for t in bucket), default=ts)
        ls = max((t.last_seen_ts for t in bucket), default=ts)
        hl = sum(t.half_life_est_s for t in bucket) / max(1, len(bucket))

        unit_id = _sha(f"{run_id}:{label}:{fs}:{ls}")[:16]
        units.append(
            MimeticWeatherUnit(
                unit_id=unit_id,
                label=label,
                kind="mimetic_weather_front",
                intensity=float(inten),
                direction=direction,
                confidence=float(conf),
                first_seen_ts=str(fs),
                last_seen_ts=str(ls),
                horizon_tags=_horizon_tags(float(hl)),
                supporting_terms=[t.term for t in bucket[:12]],
                disinfo_metrics={
                    "manipulation_risk_mean": float(risk),
                    "deepfake_pollution_risk": float(min(1.0, risk + 0.15))
                    if label == "disinfo_fog"
                    else float(max(0.0, risk - 0.1)),
                },
                provenance={"method": "build_mimetic_weather.v0.1", "ts": ts},
            )
        )

    units.sort(key=lambda u: (-u.intensity, u.label))
    return units
