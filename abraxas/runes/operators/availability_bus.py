"""ABX-Rune Operator: RUNE.AVAILABILITY_BUS (AVL).

Shadow typed stub only. Placeholder types stay NOT_COMPUTABLE.
Access/reportability/availability only. Does not invent scores, write
Active status, wire Forecast, or equate with RUNE.CHRONO_PACKET.
"""

from __future__ import annotations

from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.AVAILABILITY_BUS"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"
DISTINCT_FROM = "RUNE.CHRONO_PACKET"

_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"
_FLAG_AVAILABILITY_NOT_COMPUTABLE = "availability_not_computable"
_FLAG_WEAK = "placeholder_or_weak_input"
_FLAG_PHENOMENOLOGY = "phenomenology_claim"
_FLAG_CONSCIOUSNESS_MODULE = "consciousness_module_naming"
_FLAG_HONESTY_HOLD = "honesty_hold"
_FLAG_REGISTRY_ID_MISSING = "registry_id_missing"
_FLAG_ACTIVE_WITHOUT_HUMAN_YES = "active_without_human_yes"

_ADMISSION_ID_KEYS = ("id", "registry_id", "registryId", "rune_id", "runeId")
_HOLD_TOKENS = frozenset({"hold", "honesty_hold", "blocked"})
_CLEAR_TOKENS = frozenset({"clear", "pass", "ok", "admit"})
_ACTIVE_TOKENS = frozenset(
    {
        "active",
        "canary",
        "canon-active",
        "canon_active",
        "canonactive",
        "forecast-active",
        "forecast_active",
    }
)
_PROMOTION_LANE_KEYS = (
    "lane",
    "target_lane",
    "targetLane",
    "to_lane",
    "toLane",
    "status",
    "promotion",
    "promotion_state",
    "promotionState",
)
_HUMAN_YES_KEYS = ("human_yes", "humanYes", "danny_human_yes", "dannyHumanYes")
_HUMAN_YES_TOKENS = frozenset({"yes", "human-yes", "human_yes", "true"})
_PHENOMENOLOGY_TOKENS = (
    "phenomenology",
    "phenomenological",
    "phenomenal",
    "qualia",
    "quale",
    "sentience",
    "sentient",
    "hard problem",
    "hard_problem",
)
_CONSCIOUSNESS_TOKENS = (
    "consciousness module",
    "consciousness_module",
    "consciousness-module",
    "consciousnessmodule",
    "consciousness",
)
_CONTRACT_OUTPUT_KEYS = {
    "availability_packet": "availabilityPacket",
    "access_report": "accessReport",
    "seal_receipt": "sealReceipt",
    "eviction_receipt": "evictionReceipt",
}


class RegistryAdmissionStub(BaseModel):
    """Placeholder RegistryAdmission. NOT_COMPUTABLE. Not a registry write."""

    type_name: Literal["RegistryAdmission"] = "RegistryAdmission"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    registry_id: str | None = None


class HonestyVerdictStub(BaseModel):
    """Placeholder HonestyVerdict. NOT_COMPUTABLE. Not an honesty engine."""

    type_name: Literal["HonestyVerdict"] = "HonestyVerdict"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    hold: bool | None = None
    score: None = None


class AvailabilityPacketStub(BaseModel):
    """Placeholder AvailabilityPacket. NOT_COMPUTABLE. Access/reportability only."""

    type_name: Literal["AvailabilityPacket"] = "AvailabilityPacket"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    admitted_id: str | None = None
    availability: None = None
    access: None = None
    not_computable_flags: list[str] = Field(default_factory=list)


class AccessReportStub(BaseModel):
    """Placeholder AccessReport. NOT_COMPUTABLE. Reportability only."""

    type_name: Literal["AccessReport"] = "AccessReport"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    reportable: bool | None = None
    access_only: Literal[True] = True
    claim: None = None
    not_computable_flags: list[str] = Field(default_factory=list)


class SealReceiptStub(BaseModel):
    """Placeholder SealReceipt. NOT_COMPUTABLE. Not a Timechain write."""

    type_name: Literal["SealReceipt"] = "SealReceipt"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    sealed: bool | None = None
    receipt_id: None = None
    not_computable_flags: list[str] = Field(default_factory=list)


class EvictionReceiptStub(BaseModel):
    """Placeholder EvictionReceipt. NOT_COMPUTABLE. Optional; unused on stub path."""

    type_name: Literal["EvictionReceipt"] = "EvictionReceipt"
    status: Literal["NOT_COMPUTABLE"] = "NOT_COMPUTABLE"
    evicted: None = None
    reason: None = None


class AvailabilityBusProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: None = None


class AvailabilityBusResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    availability_packet: AvailabilityPacketStub
    access_report: AccessReportStub
    seal_receipt: SealReceiptStub
    eviction_receipt: EvictionReceiptStub | None = None
    provenance: AvailabilityBusProvenance


def admit(
    registry_admission: object,
    shadow_honesty_verdict: object,
    *,
    promotion_event: object = None,
    drift_parity: object = None,
    chrono_packet: object = None,
    timechain_seal: object = None,
    prism_card_lifecycle: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> AvailabilityBusResult:
    """Accept registryAdmission + shadowHonestyVerdict. Never invent availability."""
    del strict_execution
    path = ["parse_inputs"]
    caller_ts = _optional_string(timestamp)
    input_hash = _input_hash(
        registry_admission,
        shadow_honesty_verdict,
        promotion_event,
        drift_parity,
        chrono_packet,
        timechain_seal,
        prism_card_lifecycle,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    claim_flags = _scan_claim_flags(
        registry_admission,
        shadow_honesty_verdict,
        promotion_event,
        drift_parity,
        chrono_packet,
        timechain_seal,
        prism_card_lifecycle,
    )
    admission, admission_ok, admission_weak, admission_id = _parse_admission(registry_admission)
    honesty, honesty_ok, honesty_weak, honesty_hold = _parse_honesty(shadow_honesty_verdict)
    promotion, promotion_ok, active_without_yes = _parse_promotion(promotion_event)
    extras_ok = _optional_mappings_ok(drift_parity, chrono_packet, timechain_seal, prism_card_lifecycle)

    flags = [_FLAG_NOT_COMPUTABLE, _FLAG_AVAILABILITY_NOT_COMPUTABLE]
    fail_closed = False
    if claim_flags:
        flags.extend(sorted(claim_flags))
        path.append("fail_closed_claim_language")
        fail_closed = True
    if not admission_ok or admission_id is None:
        flags.append(_FLAG_REGISTRY_ID_MISSING)
        path.append("fail_closed_registry_id_missing")
        fail_closed = True
    if not honesty_ok or honesty_hold:
        flags.append(_FLAG_HONESTY_HOLD)
        path.append("fail_closed_honesty_hold")
        fail_closed = True
    if active_without_yes:
        flags.append(_FLAG_ACTIVE_WITHOUT_HUMAN_YES)
        path.append("fail_closed_active_without_human_yes")
        fail_closed = True
    if not extras_ok or not promotion_ok:
        path.extend(["reject_schema", "not_computable"])
        flags.append(_FLAG_WEAK)
        return _stub_result(
            flags=flags,
            path=path,
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
            admitted_id=None,
            reportable=False,
            sealed=False,
        )

    path.append("typed_stub")
    if admission_weak or honesty_weak or admission is None or honesty is None:
        flags.append(_FLAG_WEAK)
        path.append("weak_or_placeholder")
    if fail_closed:
        path.append("fail_closed")
        echoed_id = None
        reportable: bool | None = False
        sealed: bool | None = False
    else:
        echoed_id = admission_id
        reportable = None
        sealed = None
    path.append("not_computable")
    return _stub_result(
        flags=flags,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
        admitted_id=echoed_id,
        reportable=reportable,
        sealed=sealed,
    )


def apply_availability_bus(
    registryAdmission: object = None,
    shadowHonestyVerdict: object = None,
    promotionEvent: object = None,
    driftParity: object = None,
    chronoPacket: object = None,
    timechainSeal: object = None,
    prismCardLifecycle: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    registry_admission: object = None,
    shadow_honesty_verdict: object = None,
    promotion_event: object = None,
    drift_parity: object = None,
    chrono_packet: object = None,
    timechain_seal: object = None,
    prism_card_lifecycle: object = None,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; admit() is the typed API."""
    result = admit(
        registryAdmission if registryAdmission is not None else registry_admission,
        shadowHonestyVerdict if shadowHonestyVerdict is not None else shadow_honesty_verdict,
        promotion_event=promotionEvent if promotionEvent is not None else promotion_event,
        drift_parity=driftParity if driftParity is not None else drift_parity,
        chrono_packet=chronoPacket if chronoPacket is not None else chrono_packet,
        timechain_seal=timechainSeal if timechainSeal is not None else timechain_seal,
        prism_card_lifecycle=prismCardLifecycle if prismCardLifecycle is not None else prism_card_lifecycle,
        seed=seed,
        run_id=run_id,
        timestamp=timestamp,
        catalog_hash=catalog_hash,
        strict_execution=strict_execution,
    )
    return _dump_contract(result)


def _dump_contract(result: AvailabilityBusResult) -> dict[str, object]:
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


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _echo_id(mapping: Mapping[str, object], keys: tuple[str, ...] = _ADMISSION_ID_KEYS) -> str | None:
    for key in keys:
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


def _optional_mapping(raw: object) -> tuple[Mapping[str, object] | None, bool, bool]:
    if raw is None:
        return None, True, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True
    return mapping, True, _is_placeholder_mapping(mapping)


def _optional_mappings_ok(*raws: object) -> bool:
    for raw in raws:
        _mapping, ok, _weak = _optional_mapping(raw)
        if not ok:
            return False
    return True


def _parse_admission(raw: object) -> tuple[RegistryAdmissionStub | None, bool, bool, str | None]:
    if raw is None:
        return None, True, True, None
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True, None
    registry_id = _echo_id(mapping)
    return RegistryAdmissionStub(registry_id=registry_id), True, _is_placeholder_mapping(mapping), registry_id


def _token(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip().lower().replace(" ", "_")
    return None


def _parse_honesty(raw: object) -> tuple[HonestyVerdictStub | None, bool, bool, bool]:
    if raw is None:
        return None, True, True, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, True, True
    hold = _honesty_is_hold(mapping)
    return HonestyVerdictStub(hold=hold), True, _is_placeholder_mapping(mapping), hold


def _honesty_is_hold(mapping: Mapping[str, object]) -> bool:
    if mapping.get("hold") is True or mapping.get("honesty_hold") is True:
        return True
    axes = mapping.get("axes")
    if isinstance(axes, Mapping) and axes.get("hold") is True:
        return True
    saw_hold = False
    saw_clear = False
    for key in ("status", "verdict", "result", "honesty"):
        token = _token(mapping.get(key))
        if token in _HOLD_TOKENS:
            saw_hold = True
        if token in _CLEAR_TOKENS:
            saw_clear = True
    if saw_hold:
        return True
    if saw_clear:
        return False
    return True


def _parse_promotion(raw: object) -> tuple[Mapping[str, object] | None, bool, bool]:
    if raw is None:
        return None, True, False
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False, False
    return mapping, True, _active_without_human_yes(mapping)


def _human_yes(mapping: Mapping[str, object]) -> bool:
    for key in _HUMAN_YES_KEYS:
        value = mapping.get(key)
        if value is True:
            return True
        token = _token(value)
        if token in _HUMAN_YES_TOKENS:
            return True
    return False


def _active_without_human_yes(mapping: Mapping[str, object]) -> bool:
    claims_active = False
    for key in _PROMOTION_LANE_KEYS:
        token = _token(mapping.get(key))
        if token in _ACTIVE_TOKENS:
            claims_active = True
            break
    if not claims_active:
        return False
    return not _human_yes(mapping)


def _walk_strings(raw: object) -> list[str]:
    out: list[str] = []
    if raw is None or isinstance(raw, bool):
        return out
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Mapping):
        for key, value in raw.items():
            if isinstance(key, str):
                out.append(key)
            out.extend(_walk_strings(value))
        return out
    if isinstance(raw, Sequence) and not isinstance(raw, (bytes, bytearray)):
        for item in raw:
            out.extend(_walk_strings(item))
    return out


def _normalized_text(value: str) -> str:
    lowered = value.lower().replace("_", " ").replace("-", " ")
    return " ".join(lowered.split())


def _scan_claim_flags(*raws: object) -> set[str]:
    flags: set[str] = set()
    for raw in raws:
        for text in _walk_strings(raw):
            collapsed = _normalized_text(text)
            if any(token.replace("_", " ").replace("-", " ") in collapsed for token in _CONSCIOUSNESS_TOKENS):
                flags.add(_FLAG_CONSCIOUSNESS_MODULE)
            if any(token.replace("_", " ").replace("-", " ") in collapsed for token in _PHENOMENOLOGY_TOKENS):
                flags.add(_FLAG_PHENOMENOLOGY)
    return flags


def _canonical_mapping(raw: object) -> object:
    mapping = _as_mapping(raw)
    return dict(mapping) if mapping is not None else None


def _input_hash(
    registry_admission: object,
    shadow_honesty_verdict: object,
    promotion_event: object,
    drift_parity: object,
    chrono_packet: object,
    timechain_seal: object,
    prism_card_lifecycle: object,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "chrono_packet": _canonical_mapping(chrono_packet),
        "drift_parity": _canonical_mapping(drift_parity),
        "prism_card_lifecycle": _canonical_mapping(prism_card_lifecycle),
        "promotion_event": _canonical_mapping(promotion_event),
        "registry_admission": _canonical_mapping(registry_admission),
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "shadow_honesty_verdict": _canonical_mapping(shadow_honesty_verdict),
        "timechain_seal": _canonical_mapping(timechain_seal),
        "timestamp": timestamp,
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
    admitted_id: str | None,
    reportable: bool | None,
    sealed: bool | None,
) -> AvailabilityBusResult:
    unique = _unique_flags(flags)
    packet = AvailabilityPacketStub(admitted_id=admitted_id, not_computable_flags=unique)
    report = AccessReportStub(reportable=reportable, not_computable_flags=unique)
    seal = SealReceiptStub(sealed=sealed, not_computable_flags=unique)
    eviction = EvictionReceiptStub()
    body = {
        "access_report": report.model_dump(),
        "availability_packet": packet.model_dump(),
        "eviction_receipt": eviction.model_dump(),
        "seal_receipt": seal.model_dump(),
    }
    provenance = AvailabilityBusProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=sha256_hex(canonical_json(body)),
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
    )
    return AvailabilityBusResult(
        availability_packet=packet,
        access_report=report,
        seal_receipt=seal,
        eviction_receipt=eviction,
        provenance=provenance,
    )
