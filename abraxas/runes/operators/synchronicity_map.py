"""ABX-Rune Operator: ϟ₁₀ SYNCHRONICITY_MAP."""

from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import TVM_VECTOR_IDS, _round_float


class SynchronicityMetrics(BaseModel):
    TCI: Optional[float] = Field(None, description="Temporal Coincidence Index")
    SIS: Optional[float] = Field(None, description="Symbolic Isomorphism Score")
    CPA: Optional[float] = Field(None, description="Cycle Phase Alignment")
    RAC: Optional[float] = Field(None, description="Rarity-Adjusted Convergence")
    PUR: Optional[float] = Field(None, description="Persistence Under Rerun")
    not_computable: List[str] = Field(default_factory=list)


class SynchronicityEnvelope(BaseModel):
    domains_involved: Tuple[str, str]
    vectors_activated: List[str]
    metrics: SynchronicityMetrics
    time_window: str
    rarity_estimate: Optional[float]
    persistence_score: Optional[float]
    provenance: Dict[str, Any]


class SynchronicityCluster(BaseModel):
    cluster_id: str
    domain: str = Field(default="unknown")
    motifs: List[str] = Field(default_factory=list)
    edges: List[str] = Field(default_factory=list)
    strength: float = Field(default=0.0)
    window_start_utc: Optional[str] = None
    window_end_utc: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)


class SynchronicityBundle(BaseModel):
    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    stage: str = Field(
        default="envelope",
        description="Contract stage: envelope (pre-topology) or clustered (topology-aware)",
    )
    envelopes: List[SynchronicityEnvelope] = Field(default_factory=list)
    clusters: List[SynchronicityCluster] = Field(default_factory=list)
    not_computable: bool = Field(False, description="True if no synchronicity could be computed")
    not_computable_detail: Optional[Dict[str, Any]] = Field(
        None, description="Structured not_computable detail"
    )
    provenance: Dict[str, Any] = Field(default_factory=dict)


def _parse_timestamp(value: Any) -> Optional[str]:
    if isinstance(value, str) and value:
        return value
    return None


def _sort_frames(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(frames, key=lambda f: _parse_timestamp(f.get("provenance", {}).get("timestamp_utc") or f.get("timestamp_utc")) or "")


def _latest_frame(frames: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not frames:
        return None
    return _sort_frames(frames)[-1]


def _metric_sis(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[float]:
    diffs = []
    for vid in TVM_VECTOR_IDS:
        av = a.get(vid.value)
        bv = b.get(vid.value)
        if av is None or bv is None:
            continue
        diffs.append(abs(float(av) - float(bv)))
    if not diffs:
        return None
    return max(0.0, 1.0 - (sum(diffs) / len(diffs)))


def _metric_tci(ts_a: Optional[str], ts_b: Optional[str], window_seconds: int) -> Optional[float]:
    if not ts_a or not ts_b:
        return None
    try:
        dt_a = _to_epoch(ts_a)
        dt_b = _to_epoch(ts_b)
    except ValueError:
        return None
    diff = abs(dt_a - dt_b)
    if window_seconds <= 0:
        return None
    return max(0.0, 1.0 - min(diff / window_seconds, 1.0))


def _metric_cpa(frames_a: List[Dict[str, Any]], frames_b: List[Dict[str, Any]]) -> Optional[float]:
    if len(frames_a) < 2 or len(frames_b) < 2:
        return None
    phase_a = _phase_position(frames_a)
    phase_b = _phase_position(frames_b)
    if phase_a is None or phase_b is None:
        return None
    return max(0.0, 1.0 - abs(phase_a - phase_b))


def _metric_rac(a: Dict[str, Any], b: Dict[str, Any]) -> Optional[float]:
    matches = 0
    total = 0
    for vid in TVM_VECTOR_IDS:
        av = a.get(vid.value)
        bv = b.get(vid.value)
        if av is None or bv is None:
            continue
        total += 1
        if abs(float(av) - float(bv)) <= 0.05:
            matches += 1
    if total == 0:
        return None
    return matches / float(total)


def _metric_pur(frames_a: List[Dict[str, Any]], frames_b: List[Dict[str, Any]]) -> Optional[float]:
    if len(frames_a) < 2 or len(frames_b) < 2:
        return None
    sig_a = _signature(frames_a[-1].get("vectors") or {})
    prev_a = _signature(frames_a[-2].get("vectors") or {})
    sig_b = _signature(frames_b[-1].get("vectors") or {})
    prev_b = _signature(frames_b[-2].get("vectors") or {})
    return 1.0 if sig_a == prev_a and sig_b == prev_b else 0.0


def _signature(vectors: Dict[str, Any]) -> Tuple[Tuple[str, float], ...]:
    items = []
    for vid in TVM_VECTOR_IDS:
        val = vectors.get(vid.value)
        if val is None:
            continue
        items.append((vid.value, _round_float(float(val))))
    return tuple(items)


def _phase_position(frames: List[Dict[str, Any]]) -> Optional[float]:
    timestamps = [
        _parse_timestamp(f.get("provenance", {}).get("timestamp_utc") or f.get("timestamp_utc"))
        for f in frames
    ]
    timestamps = [t for t in timestamps if t]
    if len(timestamps) < 2:
        return None
    ts_sorted = sorted(timestamps)
    start = _to_epoch(ts_sorted[0])
    end = _to_epoch(ts_sorted[-1])
    if end == start:
        return None
    latest = _to_epoch(ts_sorted[-1])
    return (latest - start) / float(end - start)


def _to_epoch(ts: str) -> float:
    return _parse_iso(ts).timestamp()


def _parse_iso(ts: str):
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return __import__("datetime").datetime.fromisoformat(ts)


def apply_synchronicity_map(frames: List[Dict[str, Any]], *, strict_execution: bool = False) -> Dict[str, Any]:
    """Apply SYNCHRONICITY_MAP rune operator."""
    if frames is None:
        if strict_execution:
            raise NotImplementedError("SYNCHRONICITY_MAP requires frames")
        bundle = SynchronicityBundle(
            envelopes=[],
            clusters=[],
            not_computable=True,
            not_computable_detail={
                "reason": "missing required inputs",
                "missing_inputs": ["frames"],
            },
            provenance={"inputs_hash": sha256_hex(canonical_json({"frames": []}))},
        )
        return bundle.model_dump()

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for frame in frames or []:
        domain = str(frame.get("domain") or "unknown")
        grouped.setdefault(domain, []).append(frame)

    envelopes: List[SynchronicityEnvelope] = []
    domains = sorted(grouped.keys())
    window_seconds = 86400

    for dom_a, dom_b in combinations(domains, 2):
        frames_a = _sort_frames(grouped[dom_a])
        frames_b = _sort_frames(grouped[dom_b])
        latest_a = _latest_frame(frames_a)
        latest_b = _latest_frame(frames_b)
        vec_a = (latest_a or {}).get("vectors") or {}
        vec_b = (latest_b or {}).get("vectors") or {}

        tci = _metric_tci(
            _parse_timestamp((latest_a or {}).get("provenance", {}).get("timestamp_utc") or (latest_a or {}).get("timestamp_utc")),
            _parse_timestamp((latest_b or {}).get("provenance", {}).get("timestamp_utc") or (latest_b or {}).get("timestamp_utc")),
            window_seconds,
        )
        sis = _metric_sis(vec_a, vec_b)
        cpa = _metric_cpa(frames_a, frames_b)
        rac = _metric_rac(vec_a, vec_b)
        pur = _metric_pur(frames_a, frames_b)

        metrics = SynchronicityMetrics(TCI=tci, SIS=sis, CPA=cpa, RAC=rac, PUR=pur)
        for key, value in (
            ("TCI", tci),
            ("SIS", sis),
            ("CPA", cpa),
            ("RAC", rac),
            ("PUR", pur),
        ):
            if value is None:
                metrics.not_computable.append(key)
        metrics.not_computable.sort()

        activated = []
        for vid in TVM_VECTOR_IDS:
            av = vec_a.get(vid.value)
            bv = vec_b.get(vid.value)
            if av is None or bv is None:
                continue
            if abs(float(av) - float(bv)) <= 0.05:
                activated.append(vid.value)

        provenance = {
            "inputs_hash": sha256_hex(canonical_json({"domain_a": dom_a, "domain_b": dom_b, "frames": [frames_a, frames_b]})),
            "metrics": ["TCI", "SIS", "CPA", "RAC", "PUR"],
        }

        envelope = SynchronicityEnvelope(
            domains_involved=(dom_a, dom_b),
            vectors_activated=activated,
            metrics=metrics,
            time_window=f"{window_seconds}s",
            rarity_estimate=None if rac is None else max(0.0, 1.0 - rac),
            persistence_score=pur,
            provenance=provenance,
        )
        envelopes.append(envelope)

    if not envelopes and domains:
        for dom in domains:
            envelope = SynchronicityEnvelope(
                domains_involved=(dom, dom),
                vectors_activated=[],
                metrics=SynchronicityMetrics(not_computable=["TCI", "SIS", "CPA", "RAC", "PUR"]),
                time_window=f"{window_seconds}s",
                rarity_estimate=None,
                persistence_score=None,
                provenance={"inputs_hash": sha256_hex(canonical_json({"domain": dom, "frames": grouped[dom]}))},
            )
            envelopes.append(envelope)

    bundle = SynchronicityBundle(
        stage="envelope",
        envelopes=envelopes,
        not_computable=not domains,
        provenance={"inputs_hash": sha256_hex(canonical_json({"frames": frames or []}))},
    )
    return bundle.model_dump()
