"""ABX-Rune Operator: RUNE.MEMETIC (MEM).

Shadow typed stub only. Placeholder types stay NOT_COMPUTABLE.
Does not invent Vernacular rows, wire Forecast, or merge ϟ_MEMETIC_*.
"""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.MEMETIC"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"
DISTINCT_FROM = "ϟ_MEMETIC_*"

_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"
_FLAG_CONTAMINATION = "contamination_not_computable"
_FLAG_MISSING_LINEAGE = "missing_slang_or_eco_lineage"
_FLAG_CLUSTER_FAIL = "cluster_formation_fail"
_FLAG_WEAK = "placeholder_or_weak_input"

_IDENTIFYING_KEYS = ("id", "event_id", "eventId", "window_id", "windowId")
_MEMETIC_CAPABILITY_PREFIX = "ϟ_MEMETIC_"


class SlangEventStub(BaseModel):
    """Placeholder SlangEvent. NOT_COMPUTABLE. Not a lexicon write."""

    type_name: Literal["SlangEvent"] = "SlangEvent"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    event_id: str | None = None
    vernacular_row: None = None


class EggcornEventStub(BaseModel):
    """Placeholder EggcornEvent. NOT_COMPUTABLE. Not a lexicon write."""

    type_name: Literal["EggcornEvent"] = "EggcornEvent"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    event_id: str | None = None
    vernacular_row: None = None


class RollingWindowSpecStub(BaseModel):
    """Placeholder RollingWindowSpec. NOT_COMPUTABLE. Not a runtime window."""

    type_name: Literal["RollingWindowSpec"] = "RollingWindowSpec"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    window_id: str | None = None


class MemeticClusterStub(BaseModel):
    """Placeholder MemeticCluster. NOT_COMPUTABLE. Not a cluster engine."""

    type_name: Literal["MemeticCluster"] = "MemeticCluster"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    cluster_id: None = None
    members: None = None
    vernacular_rows: None = None
    score: None = None


class MemeticArtifactStub(BaseModel):
    """Placeholder MemeticArtifact. NOT_COMPUTABLE. Not a runtime artifact."""

    type_name: Literal["MemeticArtifact"] = "MemeticArtifact"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    artifact_id: None = None
    payload: None = None
    vernacular_rows: None = None


class NarrativeTrackStub(BaseModel):
    """Placeholder NarrativeTrack. NOT_COMPUTABLE. Not a track engine."""

    type_name: Literal["NarrativeTrack"] = "NarrativeTrack"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    track_id: None = None
    score: None = None


class MemeticProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: None = None


class MemeticResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    memetic_cluster: MemeticClusterStub | None
    memetic_artifact: MemeticArtifactStub | None
    narrative_tracks: list[NarrativeTrackStub] | None
    vernacular_rows: None = None
    not_computable_flags: list[str] = Field(default_factory=list)
    provenance: MemeticProvenance


def detect(
    slang_events: object,
    eggcorn_events: object,
    window_spec: object,
    *,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> MemeticResult:
    """Accept slangEvents + eggcornEvents + windowSpec. Never invent Vernacular."""
    del strict_execution
    path = ["parse_inputs"]
    caller_ts = _optional_string(timestamp)
    input_hash = _input_hash(
        slang_events,
        eggcorn_events,
        window_spec,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    slang, slang_ok, slang_weak = _parse_event_list(slang_events, SlangEventStub)
    eco, eco_ok, eco_weak = _parse_event_list(eggcorn_events, EggcornEventStub)
    window, window_ok, window_weak = _parse_window_spec(window_spec)

    if not slang_ok or not eco_ok or not window_ok:
        path.extend(["reject_schema", "not_computable"])
        return _null_result(
            flags=[
                _FLAG_NOT_COMPUTABLE,
                _FLAG_CONTAMINATION,
                _FLAG_CLUSTER_FAIL,
                _FLAG_WEAK,
            ],
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    path.append("typed_stub")
    flags = [_FLAG_NOT_COMPUTABLE, _FLAG_CONTAMINATION, _FLAG_CLUSTER_FAIL]
    missing_lineage = (
        slang is None
        or eco is None
        or not slang
        or not eco
        or slang_weak
        or eco_weak
    )
    if missing_lineage:
        flags.append(_FLAG_MISSING_LINEAGE)
        path.append("missing_slang_or_eco_lineage")
    if slang_weak or eco_weak or window_weak or window is None:
        flags.append(_FLAG_WEAK)
        path.append("weak_or_placeholder")
    path.append("not_computable")

    emit_placeholders = (
        not missing_lineage
        and window is not None
        and not slang_weak
        and not eco_weak
        and not window_weak
    )
    del slang, eco, window
    if emit_placeholders:
        return _placeholder_result(
            flags=flags,
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )
    return _null_result(
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
    )


def apply_memetic(
    slangEvents: object = None,
    eggcornEvents: object = None,
    windowSpec: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    slang_events: object = None,
    eggcorn_events: object = None,
    window_spec: object = None,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; detect() is the typed API."""
    result = detect(
        slangEvents if slangEvents is not None else slang_events,
        eggcornEvents if eggcornEvents is not None else eggcorn_events,
        windowSpec if windowSpec is not None else window_spec,
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


def _as_sequence(raw: object) -> list[object] | None:
    if raw is None or isinstance(raw, (str, bytes, bytearray)):
        return None
    if isinstance(raw, Sequence):
        return list(raw)
    return None


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _echo_id(mapping: Mapping[str, object]) -> str | None:
    for key in _IDENTIFYING_KEYS:
        value = mapping.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _is_placeholder_mapping(mapping: Mapping[str, object]) -> bool:
    status = mapping.get("status")
    if status in {_FLAG_NOT_COMPUTABLE, "not_computable"}:
        return True
    if mapping.get("placeholder") is True:
        return True
    if _echo_id(mapping) is None and not any(
        key not in {"type", "type_name", "status", "placeholder"} for key in mapping
    ):
        return True
    return False


def _parse_event_list(
    raw: object, stub_cls: type[SlangEventStub] | type[EggcornEventStub]
) -> tuple[list[SlangEventStub] | list[EggcornEventStub] | None, bool, bool]:
    if raw is None:
        return None, True, True
    items = _as_sequence(raw)
    if items is None:
        return None, False, True
    parsed: list[SlangEventStub] | list[EggcornEventStub] = []
    weak = not items
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            return None, False, True
        if _is_placeholder_mapping(mapping):
            weak = True
        parsed.append(stub_cls(event_id=_echo_id(mapping)))
    return parsed, True, weak


def _parse_window_spec(raw: object) -> tuple[RollingWindowSpecStub | None, bool, bool]:
    if raw is None:
        return None, True, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True
    return RollingWindowSpecStub(window_id=_echo_id(mapping)), True, _is_placeholder_mapping(mapping)


def _canonical_events(raw: object) -> object:
    items = _as_sequence(raw)
    if items is None:
        return None
    out: list[object] = []
    for item in items:
        mapping = _as_mapping(item)
        out.append(dict(mapping) if mapping is not None else None)
    return out


def _canonical_mapping(raw: object) -> object:
    mapping = _as_mapping(raw)
    return dict(mapping) if mapping is not None else None


def _input_hash(
    slang_events: object,
    eggcorn_events: object,
    window_spec: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "eggcorn_events": _canonical_events(eggcorn_events),
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "slang_events": _canonical_events(slang_events),
        "timestamp": timestamp,
        "window_spec": _canonical_mapping(window_spec),
    }
    return sha256_hex(canonical_json(payload))


def _unique_flags(flags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def _body(
    cluster: MemeticClusterStub | None,
    artifact: MemeticArtifactStub | None,
    tracks: list[NarrativeTrackStub] | None,
    flags: list[str],
) -> dict[str, object]:
    return {
        "memetic_artifact": None if artifact is None else artifact.model_dump(),
        "memetic_cluster": None if cluster is None else cluster.model_dump(),
        "narrative_tracks": None if tracks is None else [item.model_dump() for item in tracks],
        "not_computable_flags": flags,
        "vernacular_rows": None,
    }


def _finalize(
    *,
    cluster: MemeticClusterStub | None,
    artifact: MemeticArtifactStub | None,
    tracks: list[NarrativeTrackStub] | None,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> MemeticResult:
    unique = _unique_flags(flags)
    provenance = MemeticProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=sha256_hex(canonical_json(_body(cluster, artifact, tracks, unique))),
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
    )
    return MemeticResult(
        memetic_cluster=cluster,
        memetic_artifact=artifact,
        narrative_tracks=tracks,
        vernacular_rows=None,
        not_computable_flags=unique,
        provenance=provenance,
    )


def _null_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> MemeticResult:
    return _finalize(
        cluster=None,
        artifact=None,
        tracks=None,
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
    )


def _placeholder_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> MemeticResult:
    return _finalize(
        cluster=MemeticClusterStub(),
        artifact=MemeticArtifactStub(),
        tracks=[NarrativeTrackStub()],
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
    )


def aliases_memetic_capability(rune_id: object) -> bool:
    """True if a cite is a ϟ_MEMETIC_* capability id. RUNE.MEMETIC is not one."""
    if not isinstance(rune_id, str):
        return False
    return rune_id.startswith(_MEMETIC_CAPABILITY_PREFIX)
