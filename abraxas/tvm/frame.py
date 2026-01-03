"""TVM frame composition from MetricPoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.metric_extractors.base import MetricPoint
from abraxas.schema.tvm import TVMVectorId, _round_float


class VectorValue(BaseModel):
    score: Optional[float]
    computability: str
    evidence_refs: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class TVMFrame(BaseModel):
    window_start_utc: str
    window_end_utc: str
    vectors: Dict[str, VectorValue]
    provenance: Dict[str, Any]

    def frame_hash(self) -> str:
        payload = self.model_dump()
        return sha256_hex(canonical_json(payload))


def _scale_to_unit(value: float, max_value: float) -> float:
    return max(0.0, min(1.0, value / max_value))


def compose_frames(points: List[MetricPoint], *, window_start_utc: str, window_end_utc: str) -> TVMFrame:
    vectors: Dict[str, VectorValue] = {}
    evidence = {point.metric_id: point.point_hash() for point in points}

    def value_for(metric_id: str) -> Optional[float]:
        for point in points:
            if point.metric_id == metric_id and isinstance(point.value, (int, float)):
                return float(point.value)
        return None

    def value_for_any(metric_ids: List[str]) -> Optional[float]:
        for metric_id in metric_ids:
            val = value_for(metric_id)
            if val is not None:
                return val
        return None

    # V1: signal density from token counts/duplication
    token_count = value_for_any(["linguistics.token_count_total"])
    item_count = value_for_any(["linguistics.item_count"])
    if token_count is None and item_count is None:
        vectors[TVMVectorId.V1_SIGNAL_DENSITY.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="linguistic metrics missing",
        )
    else:
        density = _scale_to_unit((token_count or 0) + (item_count or 0), 5000.0)
        vectors[TVMVectorId.V1_SIGNAL_DENSITY.value] = VectorValue(
            score=_round_float(density),
            computability="computed",
            evidence_refs=["linguistics.token_count_total", "linguistics.item_count"],
        )

    # V2: signal integrity from unique ratio + citation proxy (using duplication rate inverse)
    unique_ratio = value_for_any(["linguistics.unique_token_ratio"])
    dup_rate = value_for_any(["linguistics.duplication_rate"])
    if unique_ratio is None and dup_rate is None:
        vectors[TVMVectorId.V2_SIGNAL_INTEGRITY.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="linguistic integrity metrics missing",
        )
    else:
        integrity = (unique_ratio or 0) * (1 - (dup_rate or 0))
        vectors[TVMVectorId.V2_SIGNAL_INTEGRITY.value] = VectorValue(
            score=_round_float(max(0.0, min(1.0, integrity))),
            computability="computed",
            evidence_refs=["linguistics.unique_token_ratio", "linguistics.duplication_rate"],
        )

    # V3: distribution dynamics from outrage/call-to-action rates
    outrage = value_for_any(["linguistics.outrage_lexeme_rate"])
    call_to_action = value_for_any(["linguistics.call_to_action_rate"])
    if outrage is None and call_to_action is None:
        vectors[TVMVectorId.V3_DISTRIBUTION_DYNAMICS.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="linguistic distribution metrics missing",
        )
    else:
        dynamics = (outrage or 0) + (call_to_action or 0)
        vectors[TVMVectorId.V3_DISTRIBUTION_DYNAMICS.value] = VectorValue(
            score=_round_float(max(0.0, min(1.0, dynamics))),
            computability="computed",
            evidence_refs=["linguistics.outrage_lexeme_rate", "linguistics.call_to_action_rate"],
        )

    # V4: semantic inflation from moral/buzzword rates
    moral = value_for_any(["linguistics.moral_term_saturation"])
    buzz = value_for_any(["linguistics.buzzword_rate"])
    if moral is None and buzz is None:
        vectors[TVMVectorId.V4_SEMANTIC_INFLATION.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="linguistic inflation metrics missing",
        )
    else:
        inflation = (moral or 0) + (buzz or 0)
        vectors[TVMVectorId.V4_SEMANTIC_INFLATION.value] = VectorValue(
            score=_round_float(max(0.0, min(1.0, inflation))),
            computability="computed",
            evidence_refs=["linguistics.moral_term_saturation", "linguistics.buzzword_rate"],
        )

    # V5: slang mutation from duplication inverse (proxy for novelty)
    if dup_rate is None:
        vectors[TVMVectorId.V5_SLANG_MUTATION.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="linguistic duplication metric missing",
        )
    else:
        novelty = max(0.0, min(1.0, 1 - dup_rate))
        vectors[TVMVectorId.V5_SLANG_MUTATION.value] = VectorValue(
            score=_round_float(novelty),
            computability="computed",
            evidence_refs=["linguistics.duplication_rate"],
        )

    # V6: narrative load from story arc markers
    story_arc = value_for_any(["linguistics.story_arc_marker_rate"])
    if story_arc is None:
        vectors[TVMVectorId.V6_NARRATIVE_LOAD.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="linguistic narrative metrics missing",
        )
    else:
        vectors[TVMVectorId.V6_NARRATIVE_LOAD.value] = VectorValue(
            score=_round_float(max(0.0, min(1.0, story_arc))),
            computability="computed",
            evidence_refs=["linguistics.story_arc_marker_rate"],
        )

    # V12: technical constraint from geomagnetic Kp
    kp = value_for("geomagnetic.kp_value")
    if kp is None:
        vectors[TVMVectorId.V12_TECHNICAL_CONSTRAINT.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="geomagnetic.kp_value missing",
        )
    else:
        vectors[TVMVectorId.V12_TECHNICAL_CONSTRAINT.value] = VectorValue(
            score=_round_float(_scale_to_unit(kp, 9.0)),
            computability="computed",
            evidence_refs=["geomagnetic.kp_value"],
        )

    # V15: ritual cohesion from temporal events count
    events_count = value_for("temporal.events_count")
    if events_count is None:
        vectors[TVMVectorId.V15_RITUAL_COHESION.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="temporal.events_count missing",
        )
    else:
        vectors[TVMVectorId.V15_RITUAL_COHESION.value] = VectorValue(
            score=_round_float(_scale_to_unit(events_count, 10.0)),
            computability="computed",
            evidence_refs=["temporal.events_count"],
        )

    # V7/V8: meteorology temperature anomaly
    temp_anomaly = value_for("meteorology.temperature_anomaly")
    if temp_anomaly is None:
        vectors[TVMVectorId.V7_COGNITIVE_LOAD.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="meteorology.temperature_anomaly missing",
        )
        vectors[TVMVectorId.V8_EMOTIONAL_CLIMATE.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="meteorology.temperature_anomaly missing",
        )
    else:
        normalized = _round_float(_scale_to_unit(abs(temp_anomaly), 5.0))
        vectors[TVMVectorId.V7_COGNITIVE_LOAD.value] = VectorValue(
            score=normalized,
            computability="computed",
            evidence_refs=["meteorology.temperature_anomaly"],
        )
        vectors[TVMVectorId.V8_EMOTIONAL_CLIMATE.value] = VectorValue(
            score=normalized,
            computability="computed",
            evidence_refs=["meteorology.temperature_anomaly"],
        )

    # V10: governance pressure from policy density proxy
    policy_density = value_for_any(["governance.policy_density_proxy"])
    if policy_density is None:
        vectors[TVMVectorId.V10_GOVERNANCE_PRESSURE.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="governance policy density missing",
        )
    else:
        vectors[TVMVectorId.V10_GOVERNANCE_PRESSURE.value] = VectorValue(
            score=_round_float(max(0.0, min(1.0, policy_density))),
            computability="computed",
            evidence_refs=["governance.policy_density_proxy"],
        )

    # V11: economic stress from cost of living/labor/inflation proxies
    econ_values = [
        value_for_any(["economics.cost_of_living_delta_proxy"]),
        value_for_any(["economics.labor_volatility_proxy"]),
        value_for_any(["economics.inflation_rate_proxy"]),
    ]
    econ_values = [val for val in econ_values if val is not None]
    if not econ_values:
        vectors[TVMVectorId.V11_ECONOMIC_STRESS.value] = VectorValue(
            score=None,
            computability="not_computable",
            evidence_refs=list(evidence.keys()),
            notes="economic stress metrics missing",
        )
    else:
        econ_score = sum(abs(val) for val in econ_values) / len(econ_values)
        vectors[TVMVectorId.V11_ECONOMIC_STRESS.value] = VectorValue(
            score=_round_float(max(0.0, min(1.0, econ_score))),
            computability="computed",
            evidence_refs=[
                "economics.cost_of_living_delta_proxy",
                "economics.labor_volatility_proxy",
                "economics.inflation_rate_proxy",
            ],
        )

    for vid in TVMVectorId:
        if vid.value not in vectors:
            vectors[vid.value] = VectorValue(
                score=None,
                computability="not_computable",
                evidence_refs=list(evidence.keys()),
                notes="insufficient metrics",
            )

    provenance = {
        "metrics_hash": sha256_hex(canonical_json([point.canonical_payload() for point in points])),
        "evidence": evidence,
        "window": {"start": window_start_utc, "end": window_end_utc},
    }
    return TVMFrame(
        window_start_utc=window_start_utc,
        window_end_utc=window_end_utc,
        vectors=vectors,
        provenance=provenance,
    )
