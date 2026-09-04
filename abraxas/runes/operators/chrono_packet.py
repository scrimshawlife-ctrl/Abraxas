"""ABX-Rune Operator: RUNE.CHRONO_PACKET (CHP).

Shadow-only TemporalAlignmentPacket.v1 composer. Pure and seedable.
Combines observed + inferred + speculative without fabricating fields,
coercing speculative into observed, reading wall clock, or influencing Forecast.
"""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.CHRONO_PACKET"
RUNE_VERSION = "v0.1.0"
PACKET_TYPE = "TemporalAlignmentPacket.v1"
PACKET_VERSION = "1.0.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"

_FLAG_SCHEMA = "schema_noncompliance"
_FLAG_PROVENANCE = "missing_required_provenance"
_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"

_OBSERVED_KEYS = (
    "cadence_interval",
    "recurrence_strength",
    "window_density",
    "timing_volatility",
    "cadence_stability",
    "recurrence_pressure",
)
_INFERRED_KEYS = (
    "alignment_window",
    "execution_readiness",
    "timing_advantage_hypothesis",
    "window_decay_rate",
)
_SPECULATIVE_KEYS = (
    "symbolic_time_markers",
    "ritual_timing_notes",
)
_INCOMING_FAIL_FLAGS = frozenset(
    {
        "NOT_COMPUTABLE",
        "timestamps_missing",
        "event_density_too_weak",
        "window_config_invalid",
        "metrics_not_computable",
        "no_lawful_window",
        "policy_invalid",
        "symbolic_input_too_weak",
        "not_computable",
        "schema_noncompliance",
        "missing_required_provenance",
    }
)


class PacketObserved(BaseModel):
    cadence_interval: float | None = None
    recurrence_strength: float | None = None
    window_density: float | None = None
    timing_volatility: float | None = None
    cadence_stability: float | None = None
    recurrence_pressure: float | None = None


class PacketAlignmentWindow(BaseModel):
    start: str | None = None
    end: str | None = None
    window_label: str | None = None


class PacketInferred(BaseModel):
    alignment_window: PacketAlignmentWindow | None = None
    execution_readiness: float | None = None
    timing_advantage_hypothesis: str | None = None
    window_decay_rate: float | None = None


class PacketSpeculative(BaseModel):
    symbolic_time_markers: list[str] = Field(default_factory=list)
    ritual_timing_notes: list[str] = Field(default_factory=list)


class PacketProvenance(BaseModel):
    source_family: list[str] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    computation_path: list[str] = Field(default_factory=list)
    confidence: float | None = None
    generated_at: str | None = None


class TemporalAlignmentPacket(BaseModel):
    packet_type: Literal["TemporalAlignmentPacket.v1"] = PACKET_TYPE
    packet_version: Literal["1.0.0"] = PACKET_VERSION
    lane: Literal["SHADOW"] = LANE
    status: Literal["active", "deprecated", "shadow_only", "not_computable"]
    observed: PacketObserved
    inferred: PacketInferred
    speculative: PacketSpeculative
    provenance: PacketProvenance


class ChronoPacketProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: float | None = None


class ChronoPacketResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    temporal_alignment_packet: TemporalAlignmentPacket
    provenance: ChronoPacketProvenance


def compose(
    observed: object = None,
    inferred: object = None,
    speculative: object = None,
    provenance: object = None,
    *,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> ChronoPacketResult:
    """Emit TemporalAlignmentPacket.v1. Never fabricate or leak speculative."""
    del strict_execution
    path = ["parse_inputs"]
    caller_ts = _optional_string(timestamp)
    input_hash = _input_hash(
        observed,
        inferred,
        speculative,
        provenance,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    provenance_map, provenance_ok = _parse_required_mapping(provenance)
    if not provenance_ok:
        return _unclean_result(
            flags=[_FLAG_PROVENANCE, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_provenance", "not_computable"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
            packet_provenance=PacketProvenance(computation_path=[RUNE_ID]),
        )

    observed_block, observed_ok, observed_flags = _parse_observed(observed)
    inferred_block, inferred_ok, inferred_flags = _parse_inferred(inferred)
    speculative_block, speculative_ok, speculative_flags = _parse_speculative(speculative)
    if not (observed_ok and inferred_ok and speculative_ok):
        return _unclean_result(
            flags=[_FLAG_SCHEMA, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_schema", "not_computable"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
            packet_provenance=_packet_provenance(provenance_map, caller_ts, [RUNE_ID]),
        )

    path.append("isolate_blocks")
    incoming_flags = observed_flags | inferred_flags | speculative_flags
    packet_provenance = _packet_provenance(provenance_map, caller_ts, path)
    lawful_observed = _has_lawful_observed(observed_block)
    if incoming_flags & _INCOMING_FAIL_FLAGS or not lawful_observed:
        status: Literal["active", "not_computable"] = "not_computable"
        path.append("not_computable")
        confidence = None
    else:
        status = "active"
        path.append("emit_packet")
        confidence = packet_provenance.confidence

    packet_body = TemporalAlignmentPacket(
        status=status,
        observed=observed_block,
        inferred=inferred_block,
        speculative=speculative_block,
        provenance=packet_provenance,
    )
    return _finalize(
        packet_body,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
        confidence=confidence,
    )


def apply_chrono_packet(
    observed: object = None,
    inferred: object = None,
    speculative: object = None,
    provenance: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; compose() is the typed API."""
    result = compose(
        observed,
        inferred,
        speculative,
        provenance,
        seed=seed,
        run_id=run_id,
        timestamp=timestamp,
        catalog_hash=catalog_hash,
        strict_execution=strict_execution,
    )
    return result.model_dump()


def _as_mapping(raw: object) -> Mapping[str, object] | None:
    if isinstance(raw, Mapping):
        return raw
    dumped = getattr(raw, "model_dump", None)
    if callable(dumped):
        payload = dumped()
        if isinstance(payload, Mapping):
            return payload
    return None


def _unwrap_block(raw: object, key: str) -> object:
    if raw is None:
        return None
    nested_attr = getattr(raw, key, None)
    if nested_attr is not None and not isinstance(raw, Mapping):
        if _as_mapping(nested_attr) is not None or hasattr(nested_attr, "model_dump"):
            return nested_attr
    mapping = _as_mapping(raw)
    if mapping is None:
        return raw
    nested = mapping.get(key)
    if _as_mapping(nested) is not None:
        return nested
    return mapping


def _parse_required_mapping(raw: object) -> tuple[Mapping[str, object] | None, bool]:
    if raw is None:
        return None, False
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False
    return mapping, True


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _finite_number(raw: object) -> float | None:
    if isinstance(raw, bool) or raw is None:
        return None
    if isinstance(raw, (int, float)):
        value = float(raw)
        if value != value or value in (float("inf"), float("-inf")):
            return None
        return value
    return None


def _unit_interval(raw: object) -> tuple[float | None, bool]:
    if raw is None:
        return None, True
    value = _finite_number(raw)
    if value is None:
        return None, False
    if value < 0.0 or value > 1.0:
        return None, False
    return value, True


def _optional_number(raw: object) -> tuple[float | None, bool]:
    if raw is None:
        return None, True
    value = _finite_number(raw)
    if value is None:
        return None, False
    return value, True


def _string_list(raw: object) -> tuple[list[str], bool]:
    if raw is None:
        return [], True
    if isinstance(raw, (str, bytes, bytearray)):
        return [], False
    if not isinstance(raw, Sequence):
        return [], False
    out: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            return [], False
        if item.strip():
            out.append(item.strip())
    return out, True


def _incoming_flags(raw: object) -> set[str]:
    mapping = _as_mapping(raw)
    if mapping is None:
        return set()
    flags = mapping.get("not_computable_flags")
    if not isinstance(flags, Sequence) or isinstance(flags, (str, bytes, bytearray)):
        return set()
    return {item for item in flags if isinstance(item, str) and item}


def _parse_observed(raw: object) -> tuple[PacketObserved, bool, set[str]]:
    if raw is None:
        return PacketObserved(), True, set()
    payload = _unwrap_block(raw, "observed")
    mapping = _as_mapping(payload)
    if mapping is None:
        return PacketObserved(), False, {_FLAG_SCHEMA}
    parsed: dict[str, float | None] = {}
    for key in _OBSERVED_KEYS:
        value = mapping.get(key)
        number, ok = _optional_number(value)
        if not ok:
            return PacketObserved(), False, {_FLAG_SCHEMA}
        parsed[key] = number
    return PacketObserved(**parsed), True, _incoming_flags(payload)


def _normalize_window(raw: object) -> tuple[PacketAlignmentWindow | None, bool]:
    if raw is None:
        return None, True
    if isinstance(raw, str):
        label = raw.strip()
        if not label:
            return None, True
        return PacketAlignmentWindow(window_label=label), True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False
    start = mapping.get("start")
    end = mapping.get("end")
    label = mapping.get("window_label")
    if start is not None and not isinstance(start, str):
        return None, False
    if end is not None and not isinstance(end, str):
        return None, False
    if label is not None and not isinstance(label, str):
        return None, False
    window = PacketAlignmentWindow(
        start=_optional_string(start),
        end=_optional_string(end),
        window_label=_optional_string(label),
    )
    if window.start is None and window.end is None and window.window_label is None:
        return None, True
    return window, True


def _parse_inferred(raw: object) -> tuple[PacketInferred, bool, set[str]]:
    if raw is None:
        return PacketInferred(), True, set()
    payload = _unwrap_block(raw, "inferred")
    mapping = _as_mapping(payload)
    if mapping is None:
        return PacketInferred(), False, {_FLAG_SCHEMA}
    window, window_ok = _normalize_window(mapping.get("alignment_window"))
    if not window_ok:
        return PacketInferred(), False, {_FLAG_SCHEMA}
    readiness, readiness_ok = _readiness(mapping.get("execution_readiness"))
    if not readiness_ok:
        return PacketInferred(), False, {_FLAG_SCHEMA}
    hypothesis = mapping.get("timing_advantage_hypothesis")
    if hypothesis is not None and not isinstance(hypothesis, str):
        return PacketInferred(), False, {_FLAG_SCHEMA}
    decay, decay_ok = _unit_interval(mapping.get("window_decay_rate"))
    if not decay_ok:
        return PacketInferred(), False, {_FLAG_SCHEMA}
    return (
        PacketInferred(
            alignment_window=window,
            execution_readiness=readiness,
            timing_advantage_hypothesis=_optional_string(hypothesis),
            window_decay_rate=decay,
        ),
        True,
        _incoming_flags(payload),
    )


def _readiness(raw: object) -> tuple[float | None, bool]:
    if raw is None:
        return None, True
    if isinstance(raw, str):
        # ALIGN emits shadow labels. Do not coerce them into a score.
        return None, True
    return _unit_interval(raw)


def _parse_speculative(raw: object) -> tuple[PacketSpeculative, bool, set[str]]:
    if raw is None:
        return PacketSpeculative(), True, set()
    payload = _unwrap_block(raw, "speculative")
    mapping = _as_mapping(payload)
    if mapping is None:
        return PacketSpeculative(), False, {_FLAG_SCHEMA}
    markers, markers_ok = _string_list(mapping.get("symbolic_time_markers"))
    notes, notes_ok = _string_list(mapping.get("ritual_timing_notes"))
    if not markers_ok or not notes_ok:
        return PacketSpeculative(), False, {_FLAG_SCHEMA}
    return (
        PacketSpeculative(symbolic_time_markers=markers, ritual_timing_notes=notes),
        True,
        _incoming_flags(payload),
    )


def _has_lawful_observed(observed: PacketObserved) -> bool:
    return any(
        getattr(observed, key) is not None
        for key in _OBSERVED_KEYS
    )


def _packet_provenance(
    mapping: Mapping[str, object],
    caller_ts: str | None,
    path: list[str],
) -> PacketProvenance:
    families, families_ok = _string_list(mapping.get("source_family"))
    if not families_ok:
        families, _ = _string_list(mapping.get("source_family_trace"))
    ids, ids_ok = _string_list(mapping.get("source_ids"))
    if not ids_ok:
        ids = []
    incoming_path, path_ok = _string_list(mapping.get("computation_path"))
    if not path_ok:
        incoming_path = []
    composed = list(incoming_path)
    if RUNE_ID not in composed:
        composed.append(RUNE_ID)
    confidence, confidence_ok = _unit_interval(mapping.get("confidence"))
    if not confidence_ok:
        confidence = None
    generated = _optional_string(mapping.get("generated_at")) or caller_ts
    return PacketProvenance(
        source_family=families,
        source_ids=ids,
        computation_path=composed,
        confidence=confidence,
        generated_at=generated,
    )


def _canonical_block(raw: object, key: str, keys: tuple[str, ...]) -> object:
    if raw is None:
        return None
    payload = _unwrap_block(raw, key)
    mapping = _as_mapping(payload)
    if mapping is None:
        return None
    selected = {item: mapping.get(item) for item in (*keys, "not_computable_flags")}
    return selected


def _canonical_provenance(raw: object) -> object:
    mapping = _as_mapping(raw)
    if mapping is None:
        return None
    return {
        "catalog_hash": mapping.get("catalog_hash"),
        "computation_path": mapping.get("computation_path"),
        "confidence": mapping.get("confidence"),
        "generated_at": mapping.get("generated_at"),
        "run_id": mapping.get("run_id"),
        "source_family": mapping.get("source_family") or mapping.get("source_family_trace"),
        "source_ids": mapping.get("source_ids"),
        "timestamp": mapping.get("timestamp"),
    }


def _input_hash(
    observed: object,
    inferred: object,
    speculative: object,
    provenance: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "inferred": _canonical_block(inferred, "inferred", _INFERRED_KEYS),
        "observed": _canonical_block(observed, "observed", _OBSERVED_KEYS),
        "provenance": _canonical_provenance(provenance),
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "speculative": _canonical_block(speculative, "speculative", _SPECULATIVE_KEYS),
        "timestamp": timestamp,
    }
    return sha256_hex(canonical_json(payload))


def _empty_blocks() -> tuple[PacketObserved, PacketInferred, PacketSpeculative]:
    return PacketObserved(), PacketInferred(), PacketSpeculative()


def _unclean_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
    packet_provenance: PacketProvenance,
) -> ChronoPacketResult:
    del flags
    observed, inferred, speculative = _empty_blocks()
    packet = TemporalAlignmentPacket(
        status="not_computable",
        observed=observed,
        inferred=inferred,
        speculative=speculative,
        provenance=packet_provenance,
    )
    return _finalize(
        packet,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
        confidence=None,
    )


def _body_for_hash(packet: TemporalAlignmentPacket) -> dict[str, object]:
    return {
        "inferred": packet.inferred.model_dump(),
        "lane": packet.lane,
        "observed": packet.observed.model_dump(),
        "packet_type": packet.packet_type,
        "packet_version": packet.packet_version,
        "speculative": packet.speculative.model_dump(),
        "status": packet.status,
    }


def _finalize(
    packet: TemporalAlignmentPacket,
    *,
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
    confidence: float | None,
) -> ChronoPacketResult:
    output_hash = sha256_hex(canonical_json(_body_for_hash(packet)))
    rune_path = list(path)
    if RUNE_ID not in packet.provenance.computation_path:
        packet.provenance.computation_path.append(RUNE_ID)
    provenance = ChronoPacketProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=output_hash,
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=rune_path,
        confidence=confidence,
    )
    return ChronoPacketResult(
        temporal_alignment_packet=packet,
        provenance=provenance,
    )


# Isolation sentinels for tests. Packet observed never accepts these keys.
FORBIDDEN_OBSERVED_KEYS = _SPECULATIVE_KEYS
PACKET_TOP_LEVEL_KEYS = (
    "packet_type",
    "packet_version",
    "lane",
    "status",
    "observed",
    "inferred",
    "speculative",
    "provenance",
)
PACKET_STATUS_VALUES = ("active", "deprecated", "shadow_only", "not_computable")
PACKET_LANE_VALUES = ("SHADOW",)
