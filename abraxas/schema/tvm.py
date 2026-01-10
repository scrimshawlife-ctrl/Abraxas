"""TVM schema for Oracle skeleton framing."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Iterable, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

TVM_FLOAT_PRECISION = 6


class TVMVectorId(str, Enum):
    V1_SIGNAL_DENSITY = "V1_SIGNAL_DENSITY"
    V2_SIGNAL_INTEGRITY = "V2_SIGNAL_INTEGRITY"
    V3_DISTRIBUTION_DYNAMICS = "V3_DISTRIBUTION_DYNAMICS"
    V4_SEMANTIC_INFLATION = "V4_SEMANTIC_INFLATION"
    V5_SLANG_MUTATION = "V5_SLANG_MUTATION"
    V6_NARRATIVE_LOAD = "V6_NARRATIVE_LOAD"
    V7_COGNITIVE_LOAD = "V7_COGNITIVE_LOAD"
    V8_EMOTIONAL_CLIMATE = "V8_EMOTIONAL_CLIMATE"
    V9_TRUST_TOPOLOGY = "V9_TRUST_TOPOLOGY"
    V10_GOVERNANCE_PRESSURE = "V10_GOVERNANCE_PRESSURE"
    V11_ECONOMIC_STRESS = "V11_ECONOMIC_STRESS"
    V12_TECHNICAL_CONSTRAINT = "V12_TECHNICAL_CONSTRAINT"
    V13_ARCHETYPAL_ACTIVATION = "V13_ARCHETYPAL_ACTIVATION"
    V14_IDENTITY_PHASE_STATE = "V14_IDENTITY_PHASE_STATE"
    V15_RITUAL_COHESION = "V15_RITUAL_COHESION"


TVM_VECTOR_IDS: tuple[TVMVectorId, ...] = (
    TVMVectorId.V1_SIGNAL_DENSITY,
    TVMVectorId.V2_SIGNAL_INTEGRITY,
    TVMVectorId.V3_DISTRIBUTION_DYNAMICS,
    TVMVectorId.V4_SEMANTIC_INFLATION,
    TVMVectorId.V5_SLANG_MUTATION,
    TVMVectorId.V6_NARRATIVE_LOAD,
    TVMVectorId.V7_COGNITIVE_LOAD,
    TVMVectorId.V8_EMOTIONAL_CLIMATE,
    TVMVectorId.V9_TRUST_TOPOLOGY,
    TVMVectorId.V10_GOVERNANCE_PRESSURE,
    TVMVectorId.V11_ECONOMIC_STRESS,
    TVMVectorId.V12_TECHNICAL_CONSTRAINT,
    TVMVectorId.V13_ARCHETYPAL_ACTIVATION,
    TVMVectorId.V14_IDENTITY_PHASE_STATE,
    TVMVectorId.V15_RITUAL_COHESION,
)


class TVMProvenance(BaseModel):
    """Provenance metadata for TVM framing."""

    timestamp_utc: str = Field(..., description="Observation timestamp (ISO8601, Z)")
    sources: list[str] = Field(default_factory=list, description="Source identifiers/URLs")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions applied")
    run_id: str = Field(..., description="Deterministic run ID")


class TVMVectorFrame(BaseModel):
    """Serialized TVM vector frame for a domain observation."""

    schema_version: str = Field("tvm.v0.1", description="TVM schema version")
    domain: str = Field(..., description="Domain label")
    subdomain: Optional[str] = Field(None, description="Optional subdomain label")
    vectors: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Vector values keyed by TVM vector ID",
    )
    not_computable: list[str] = Field(default_factory=list, description="Vector IDs missing inputs")
    provenance: TVMProvenance = Field(..., description="Provenance bundle")

    def normalized_vectors(self) -> Dict[str, Optional[float]]:
        """Return vectors with complete TVM ordering and rounded floats."""
        return _normalize_vectors(self.vectors)

    def canonical_payload(self) -> Dict[str, Any]:
        """Return canonical payload for deterministic hashing."""
        payload = self.model_dump()
        payload["vectors"] = _normalize_vectors(payload.get("vectors") or {})
        payload["not_computable"] = sorted(set(payload.get("not_computable") or []))
        return _round_floats(payload)


def _round_float(val: float) -> float:
    return float(f"{val:.{TVM_FLOAT_PRECISION}f}")


def _round_floats(obj: Any) -> Any:
    if isinstance(obj, float):
        return _round_float(obj)
    if isinstance(obj, dict):
        return {k: _round_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v) for v in obj]
    return obj


def _normalize_vectors(vectors: Dict[str, Optional[float]] | None) -> Dict[str, Optional[float]]:
    vectors = vectors or {}
    normalized: Dict[str, Optional[float]] = {}
    for vid in TVM_VECTOR_IDS:
        key = vid.value
        val = vectors.get(key)
        if isinstance(val, float):
            normalized[key] = _round_float(val)
        elif val is None:
            normalized[key] = None
        else:
            normalized[key] = float(val) if val is not None else None
            if normalized[key] is not None:
                normalized[key] = _round_float(normalized[key])
    return normalized


def canonical_tvm_json(frame: TVMVectorFrame | Dict[str, Any]) -> str:
    """Deterministic JSON serialization for TVM frames."""
    payload = frame.canonical_payload() if isinstance(frame, TVMVectorFrame) else _round_floats(frame)
    return canonical_json(payload)


def hash_tvm_frame(frame: TVMVectorFrame | Dict[str, Any]) -> str:
    """Stable hash for TVM frames."""
    return sha256_hex(canonical_tvm_json(frame))


def build_tvm_frame(
    observation: Dict[str, Any],
    *,
    run_id: str,
    default_sources: Iterable[str] = (),
    default_assumptions: Iterable[str] = (),
) -> TVMVectorFrame:
    """Build a TVM vector frame from a structured observation.

    Observations should provide numeric vector values under keys:
      - "tvm_vectors" or "vectors" (dict of TVM vector IDs -> float)
    If vectors are missing, all vectors are marked not_computable.
    """
    vectors = observation.get("tvm_vectors") or observation.get("vectors") or {}
    sources = list(observation.get("sources") or []) or list(default_sources)
    assumptions = list(observation.get("assumptions") or []) or list(default_assumptions)
    timestamp = (
        observation.get("timestamp_utc")
        or observation.get("observed_at")
        or observation.get("time_utc")
        or "1970-01-01T00:00:00Z"
    )
    normalized_vectors = _normalize_vectors(vectors)
    not_computable = [vid.value for vid in TVM_VECTOR_IDS if normalized_vectors.get(vid.value) is None]

    return TVMVectorFrame(
        domain=str(observation.get("domain") or "unknown"),
        subdomain=observation.get("subdomain"),
        vectors=normalized_vectors,
        not_computable=not_computable,
        provenance=TVMProvenance(
            timestamp_utc=str(timestamp),
            sources=[str(s) for s in sources],
            assumptions=[str(a) for a in assumptions],
            run_id=run_id,
        ),
    )
