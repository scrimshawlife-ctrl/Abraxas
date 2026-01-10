"""ABX-Rune Operator: ϟ₈ INFLUENCE_DETECT."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.schema.tvm import TVM_VECTOR_IDS, _round_float


class InfluenceMetric(BaseModel):
    """Influence metrics for a single domain."""

    CVP: Optional[float] = Field(None, description="Cross-Vector Perturbation")
    TLL: Optional[float] = Field(None, description="Temporal Lead-Lag")
    RD: Optional[float] = Field(None, description="Recurrence Density")
    CDEC: Optional[float] = Field(None, description="Cross-Domain Echo Count")
    RRS: Optional[float] = Field(None, description="Residual Reduction Score")
    not_computable: List[str] = Field(default_factory=list)


class InfluenceBundle(BaseModel):
    """Influence metrics bundle across domains."""

    shadow_only: bool = Field(True, description="Shadow-only enforcement")
    ics: Dict[str, InfluenceMetric] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)


def _parse_timestamp(value: Any) -> str:
    if isinstance(value, str) and value:
        return value
    return "1970-01-01T00:00:00Z"


def _sort_frames(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(frames, key=lambda f: _parse_timestamp(f.get("provenance", {}).get("timestamp_utc") or f.get("timestamp_utc")))


def _vector_signature(vectors: Dict[str, Any]) -> Tuple[Tuple[str, float], ...]:
    items = []
    for vid in TVM_VECTOR_IDS:
        val = vectors.get(vid.value)
        if val is None:
            continue
        items.append((vid.value, _round_float(float(val))))
    return tuple(items)


def _mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return sum(values) / len(values)


def _compute_cvp(vectors_list: List[Dict[str, Any]]) -> Optional[float]:
    if len(vectors_list) < 2:
        return None
    deltas = []
    for prev, cur in zip(vectors_list, vectors_list[1:]):
        diffs = []
        for vid in TVM_VECTOR_IDS:
            a = prev.get(vid.value)
            b = cur.get(vid.value)
            if a is None or b is None:
                continue
            diffs.append(abs(float(b) - float(a)))
        if diffs:
            deltas.append(sum(diffs) / len(diffs))
    return _mean(deltas)


def _compute_tll(vectors_list: List[Dict[str, Any]]) -> Optional[float]:
    if len(vectors_list) < 2:
        return None
    magnitudes = []
    for prev, cur in zip(vectors_list, vectors_list[1:]):
        diffs = []
        for vid in TVM_VECTOR_IDS:
            a = prev.get(vid.value)
            b = cur.get(vid.value)
            if a is None or b is None:
                continue
            diffs.append(abs(float(b) - float(a)))
        magnitudes.append(sum(diffs) if diffs else 0.0)
    if not magnitudes:
        return None
    idx = max(range(len(magnitudes)), key=lambda i: magnitudes[i])
    if len(magnitudes) == 1:
        return 0.0
    return idx / float(len(magnitudes) - 1)


def _compute_rd(vectors_list: List[Dict[str, Any]]) -> Optional[float]:
    if not vectors_list:
        return None
    signatures = [_vector_signature(v) for v in vectors_list]
    unique = len(set(signatures))
    if len(signatures) == 0:
        return None
    return (len(signatures) - unique) / float(len(signatures))


def _compute_cdec(domain: str, latest_vectors: Dict[str, Any], latest_by_domain: Dict[str, Dict[str, Any]]) -> Optional[float]:
    if len(latest_by_domain) <= 1:
        return None
    matches = 0
    for other_domain, other_vectors in latest_by_domain.items():
        if other_domain == domain:
            continue
        overlap = 0
        for vid in TVM_VECTOR_IDS:
            a = latest_vectors.get(vid.value)
            b = other_vectors.get(vid.value)
            if a is None or b is None:
                continue
            if abs(float(a) - float(b)) <= 0.05:
                overlap += 1
        if overlap >= 3:
            matches += 1
    return float(matches)


def _compute_rrs(vectors_list: List[Dict[str, Any]]) -> Optional[float]:
    if len(vectors_list) < 3:
        return None
    deltas = []
    for prev, cur in zip(vectors_list, vectors_list[1:]):
        diffs = []
        for vid in TVM_VECTOR_IDS:
            a = prev.get(vid.value)
            b = cur.get(vid.value)
            if a is None or b is None:
                continue
            diffs.append(abs(float(b) - float(a)))
        if diffs:
            deltas.append(sum(diffs) / len(diffs))
    if len(deltas) < 2:
        return None
    mid = len(deltas) // 2
    early = _mean(deltas[:mid])
    late = _mean(deltas[mid:])
    if early is None or late is None or early == 0:
        return None
    return max(0.0, (early - late) / early)


def apply_influence_detect(frames: List[Dict[str, Any]], *, strict_execution: bool = False) -> Dict[str, Any]:
    """Apply INFLUENCE_DETECT rune operator.

    Args:
        frames: TVM vector frames
        strict_execution: If True, raises NotImplementedError for unimplemented operators
    """
    if strict_execution and frames is None:
        raise NotImplementedError("INFLUENCE_DETECT requires frames")

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for frame in frames or []:
        domain = str(frame.get("domain") or "unknown")
        grouped[domain].append(frame)

    latest_by_domain: Dict[str, Dict[str, Any]] = {}
    for domain, domain_frames in grouped.items():
        sorted_frames = _sort_frames(domain_frames)
        if sorted_frames:
            latest_by_domain[domain] = sorted_frames[-1].get("vectors") or {}

    ics: Dict[str, InfluenceMetric] = {}
    for domain, domain_frames in grouped.items():
        sorted_frames = _sort_frames(domain_frames)
        vectors_list = [f.get("vectors") or {} for f in sorted_frames]

        cvp = _compute_cvp(vectors_list)
        tll = _compute_tll(vectors_list)
        rd = _compute_rd(vectors_list)
        cdec = _compute_cdec(domain, latest_by_domain.get(domain, {}), latest_by_domain)
        rrs = _compute_rrs(vectors_list)

        metric = InfluenceMetric(CVP=cvp, TLL=tll, RD=rd, CDEC=cdec, RRS=rrs)
        for key, value in (
            ("CVP", cvp),
            ("TLL", tll),
            ("RD", rd),
            ("CDEC", cdec),
            ("RRS", rrs),
        ):
            if value is None:
                metric.not_computable.append(key)
        metric.not_computable.sort()
        ics[domain] = metric

    if not grouped:
        ics["_global"] = InfluenceMetric(not_computable=["CVP", "TLL", "RD", "CDEC", "RRS"])

    inputs_hash = sha256_hex(canonical_json({"frames": frames or []}))
    provenance = {
        "inputs_hash": inputs_hash,
        "computed_at_utc": _derive_timestamp(frames),
        "metrics": ["CVP", "TLL", "RD", "CDEC", "RRS"],
    }

    bundle = InfluenceBundle(ics=ics, provenance=provenance)
    return bundle.model_dump()


def _derive_timestamp(frames: Optional[List[Dict[str, Any]]]) -> str:
    if not frames:
        return "1970-01-01T00:00:00Z"
    timestamps = []
    for frame in frames:
        ts = frame.get("provenance", {}).get("timestamp_utc") or frame.get("timestamp_utc")
        if ts:
            timestamps.append(str(ts))
    if not timestamps:
        return "1970-01-01T00:00:00Z"
    return sorted(timestamps)[-1]
