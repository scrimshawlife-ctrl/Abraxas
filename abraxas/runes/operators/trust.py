"""ABX-Rune Operator: RUNE.TRUST (TRU).

Shadow typed stub only. Placeholder types stay NOT_COMPUTABLE.
Does not invent trust scores, wire Forecast, or merge TRUST_CUE_SCAN.
"""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.TRUST"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"
DISTINCT_FROM = "RUNE.TRUST_CUE_SCAN"

_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"
_FLAG_TRUST_NOT_COMPUTABLE = "trust_not_computable"
_FLAG_MISSING_OUTCOME = "missing_outcome_mapping"
_FLAG_WEAK = "placeholder_or_weak_input"

_IDENTIFYING_KEYS = ("id", "event_id", "eventId", "link_id", "linkId")
_CONTRACT_OUTPUT_KEYS = {
    "trust_assessment": "trustAssessment",
    "trust_state": "trustState",
    "trust_update": "trustUpdate",
}


class TrustEventStub(BaseModel):
    """Placeholder TrustEvent. NOT_COMPUTABLE. Not a schema engine."""

    type_name: Literal["TrustEvent"] = "TrustEvent"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    event_id: str | None = None
    score: None = None


class TrustStateStub(BaseModel):
    """Placeholder TrustState. NOT_COMPUTABLE. Not a schema engine."""

    type_name: Literal["TrustState"] = "TrustState"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    score: None = None


class TrustAssessmentStub(BaseModel):
    """Placeholder TrustAssessment. NOT_COMPUTABLE. Not a schema engine."""

    type_name: Literal["TrustAssessment"] = "TrustAssessment"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    score: None = None
    not_computable_flags: list[str] = Field(default_factory=list)


class TrustUpdateStub(BaseModel):
    """Placeholder TrustUpdate. NOT_COMPUTABLE. Not a schema engine."""

    type_name: Literal["TrustUpdate"] = "TrustUpdate"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    delta: None = None


class OutcomeLinkStub(BaseModel):
    """Placeholder OutcomeLink. NOT_COMPUTABLE. Not a schema engine."""

    type_name: Literal["OutcomeLink"] = "OutcomeLink"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    link_id: str | None = None


class TrustProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: None = None


class TrustResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    trust_assessment: TrustAssessmentStub
    trust_state: TrustStateStub
    trust_update: TrustUpdateStub
    provenance: TrustProvenance


def assess(
    trust_events: object,
    prior_trust_state: object,
    *,
    outcome_links: object = None,
    decay_parameters: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> TrustResult:
    """Accept ordered trustEvents + priorTrustState. Never invent scores."""
    del strict_execution
    path = ["parse_inputs"]
    caller_ts = _optional_string(timestamp)
    input_hash = _input_hash(
        trust_events,
        prior_trust_state,
        outcome_links,
        decay_parameters,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    events, events_ok, events_weak = _parse_event_list(trust_events)
    prior, prior_ok, prior_weak = _parse_prior(prior_trust_state)
    links, links_ok, links_missing = _parse_outcome_links(outcome_links)
    if not events_ok or not prior_ok or not links_ok:
        path.extend(["reject_schema", "not_computable"])
        return _stub_result(
            flags=[_FLAG_NOT_COMPUTABLE, _FLAG_TRUST_NOT_COMPUTABLE, _FLAG_WEAK],
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    path.append("typed_stub")
    flags = [_FLAG_NOT_COMPUTABLE, _FLAG_TRUST_NOT_COMPUTABLE]
    if events_weak or prior_weak or not events or prior is None:
        flags.append(_FLAG_WEAK)
        path.append("weak_or_placeholder")
    if links_missing:
        flags.append(_FLAG_MISSING_OUTCOME)
        path.append("missing_outcome_mapping")
    path.append("not_computable")
    del events, prior, links
    return _stub_result(
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
    )


def apply_trust(
    trustEvents: object = None,
    priorTrustState: object = None,
    outcomeLinks: object = None,
    decay_parameters: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    trust_events: object = None,
    prior_trust_state: object = None,
    outcome_links: object = None,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; assess() is the typed API."""
    result = assess(
        trustEvents if trustEvents is not None else trust_events,
        priorTrustState if priorTrustState is not None else prior_trust_state,
        outcome_links=outcomeLinks if outcomeLinks is not None else outcome_links,
        decay_parameters=decay_parameters,
        seed=seed,
        run_id=run_id,
        timestamp=timestamp,
        catalog_hash=catalog_hash,
        strict_execution=strict_execution,
    )
    return _dump_contract(result)


def _dump_contract(result: TrustResult) -> dict[str, object]:
    """Emit ABXRuneContract output names for registry callers."""
    dumped = result.model_dump()
    return {_CONTRACT_OUTPUT_KEYS.get(key, key): value for key, value in dumped.items()}


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


def _parse_event_list(raw: object) -> tuple[list[TrustEventStub] | None, bool, bool]:
    if raw is None:
        return None, True, True
    items = _as_sequence(raw)
    if items is None:
        return None, False, True
    parsed: list[TrustEventStub] = []
    weak = not items
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            return None, False, True
        if _is_placeholder_mapping(mapping):
            weak = True
        parsed.append(TrustEventStub(event_id=_echo_id(mapping)))
    return parsed, True, weak


def _parse_prior(raw: object) -> tuple[TrustStateStub | None, bool, bool]:
    if raw is None:
        return None, True, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True
    return TrustStateStub(), True, _is_placeholder_mapping(mapping)


def _parse_outcome_links(raw: object) -> tuple[list[OutcomeLinkStub], bool, bool]:
    if raw is None:
        return [], True, True
    items = _as_sequence(raw)
    if items is None:
        return [], False, True
    parsed: list[OutcomeLinkStub] = []
    for item in items:
        mapping = _as_mapping(item)
        if mapping is None:
            return [], False, True
        parsed.append(OutcomeLinkStub(link_id=_echo_id(mapping)))
    return parsed, True, not parsed


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
    trust_events: object,
    prior_trust_state: object,
    outcome_links: object,
    decay_parameters: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "decay_parameters": decay_parameters if isinstance(decay_parameters, Mapping) else None,
        "outcome_links": _canonical_events(outcome_links),
        "prior_trust_state": _canonical_mapping(prior_trust_state),
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "timestamp": timestamp,
        "trust_events": _canonical_events(trust_events),
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


def _stub_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> TrustResult:
    assessment = TrustAssessmentStub(not_computable_flags=_unique_flags(flags))
    state = TrustStateStub()
    update = TrustUpdateStub()
    body = {
        "trust_assessment": assessment.model_dump(),
        "trust_state": state.model_dump(),
        "trust_update": update.model_dump(),
    }
    provenance = TrustProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=sha256_hex(canonical_json(body)),
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
    )
    return TrustResult(
        trust_assessment=assessment,
        trust_state=state,
        trust_update=update,
        provenance=provenance,
    )
