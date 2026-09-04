"""ABX-Rune Operator: RUNE.CHRONO_OVERLAY (CHO).

Shadow-only speculative annotator. Pure and seedable.
Extracts explicit symbolic timing tokens. Does not read wall clock,
invent markers, write into observed/inferred, or influence Forecast.
"""

from __future__ import annotations

import re
from typing import Literal, Mapping, Sequence

from pydantic import BaseModel, Field

from abraxas.core.canonical import canonical_json, sha256_hex

RUNE_ID = "RUNE.CHRONO_OVERLAY"
RUNE_VERSION = "v0.1.0"
LANE: Literal["SHADOW"] = "SHADOW"
INFLUENCE_POLICY: Literal["NONE"] = "NONE"

_FLAG_WEAK = "symbolic_input_too_weak"
_FLAG_NOT_COMPUTABLE = "NOT_COMPUTABLE"
_FLAG_CONTEXT = "not_computable"

_ISO_DATETIME = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
)
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_EXPLICIT_MARKER = re.compile(r"marker:([A-Za-z0-9_\-]+)")

# Longer tokens first so "summer_solstice" wins over "solstice".
_KNOWN_MARKERS = (
    "summer_solstice",
    "winter_solstice",
    "spring_equinox",
    "autumn_equinox",
    "fall_equinox",
    "lunar_eclipse",
    "solar_eclipse",
    "first_quarter",
    "last_quarter",
    "new_moon",
    "full_moon",
    "new_year",
    "midsummer",
    "midwinter",
    "solstice",
    "equinox",
    "eclipse",
    "sabbath",
)

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


class ChronoOverlaySpeculative(BaseModel):
    symbolic_time_markers: list[str] = Field(default_factory=list)
    ritual_timing_notes: list[str] = Field(default_factory=list)
    not_computable_flags: list[str] = Field(default_factory=list)


class ChronoOverlayProvenance(BaseModel):
    rune_id: str = RUNE_ID
    version: str = RUNE_VERSION
    run_id: str | None = None
    input_hash: str
    output_hash: str
    catalog_hash: str | None = None
    timestamp: str | None = None
    computation_path: list[str] = Field(default_factory=list)
    confidence: float | None = None


class ChronoOverlayResult(BaseModel):
    rune_id: str = RUNE_ID
    lane: Literal["SHADOW"] = LANE
    influence_policy: Literal["NONE"] = INFLUENCE_POLICY
    speculative: ChronoOverlaySpeculative
    provenance: ChronoOverlayProvenance


def overlay(
    symbolic_inputs: object = None,
    *,
    operator_notes: object = None,
    temporal_context: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    strict_execution: bool = False,
) -> ChronoOverlayResult:
    """Emit speculative annotations. Never invent markers or leak into observed."""
    del strict_execution
    path = ["parse_inputs"]
    symbols = _string_list(symbolic_inputs)
    notes = _string_list(operator_notes)
    caller_ts = _optional_string(timestamp)
    context, context_ok = _parse_temporal_context(temporal_context)
    input_hash = _input_hash(
        symbols,
        notes,
        context if context_ok else None,
        seed,
        run_id,
        caller_ts,
        catalog_hash,
    )

    if not context_ok:
        return _empty_result(
            flags=[_FLAG_CONTEXT, _FLAG_NOT_COMPUTABLE],
            path=path + ["reject_temporal_context", "not_computable"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    path.append("extract_explicit_markers")
    markers = _extract_markers(symbols)
    path.append("collect_operator_notes")
    if not markers and not notes:
        return _empty_result(
            flags=[_FLAG_WEAK, _FLAG_NOT_COMPUTABLE],
            path=path + ["symbolic_input_too_weak"],
            input_hash=input_hash,
            run_id=run_id,
            catalog_hash=catalog_hash,
            timestamp=caller_ts,
        )

    speculative = ChronoOverlaySpeculative(
        symbolic_time_markers=markers,
        ritual_timing_notes=list(notes),
    )
    path.append("emit_speculative")
    return _finalize(
        speculative,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=caller_ts,
        confidence=_confidence(markers, notes),
    )


def apply_chrono_overlay(
    symbolic_inputs: object = None,
    operator_notes: object = None,
    temporal_context: object = None,
    seed: object = None,
    run_id: object = None,
    timestamp: object = None,
    catalog_hash: object = None,
    *,
    strict_execution: bool = False,
    **_extra: object,
) -> dict[str, object]:
    """Registry/invoke adapter. Returns a dict; overlay() is the typed API."""
    result = overlay(
        symbolic_inputs,
        operator_notes=operator_notes,
        temporal_context=temporal_context,
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


def _parse_temporal_context(raw: object) -> tuple[Mapping[str, object] | None, bool]:
    if raw is None:
        return None, True
    mapping = _as_mapping(raw)
    if mapping is None:
        return None, False
    return mapping, True


def _string_list(raw: object) -> list[str]:
    if raw is None or isinstance(raw, (str, bytes, bytearray)):
        return []
    if not isinstance(raw, Sequence):
        return []
    out: list[str] = []
    for item in raw:
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
    return out


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _extract_markers(symbols: list[str]) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for text in symbols:
        for token in _tokens_from_text(text):
            if token not in seen:
                seen.add(token)
                found.append(token)
    return found


def _tokens_from_text(text: str) -> list[str]:
    tokens: list[str] = []
    occupied: list[tuple[int, int]] = []
    for match in _ISO_DATETIME.finditer(text):
        tokens.append(match.group(0))
        occupied.append(match.span())
    for match in _ISO_DATE.finditer(text):
        if any(start <= match.start() < end for start, end in occupied):
            continue
        tokens.append(match.group(0))
        occupied.append(match.span())
    for match in _EXPLICIT_MARKER.finditer(text):
        tokens.append(f"marker:{match.group(1)}")
    lowered = text.lower()
    for name in _KNOWN_MARKERS:
        parts = name.split("_")
        joined = r"[\s_\-]+".join(re.escape(part) for part in parts)
        pattern = rf"(?<![a-z0-9]){joined}(?![a-z0-9])"
        if re.search(pattern, lowered):
            tokens.append(name)
    return tokens


def _confidence(markers: list[str], notes: list[str]) -> float:
    volume = (len(markers) + len(notes)) / 16.0
    return round(min(1.0, volume), 6)


def _unique_flags(flags: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for flag in flags:
        if flag not in seen:
            seen.add(flag)
            out.append(flag)
    return out


def _canonical_context(raw: Mapping[str, object] | None) -> object:
    if raw is None:
        return None
    # Hash identity only. Observed/inferred blocks are never copied out.
    payload: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        mapping = _as_mapping(value)
        payload[key] = dict(mapping) if mapping is not None else value
    return payload


def _input_hash(
    symbols: list[str],
    notes: list[str],
    temporal_context: Mapping[str, object] | None,
    seed: object,
    run_id: object,
    timestamp: str | None,
    catalog_hash: object,
) -> str:
    payload = {
        "catalog_hash": catalog_hash if isinstance(catalog_hash, str) else None,
        "operator_notes": notes,
        "run_id": run_id if isinstance(run_id, str) else None,
        "seed": seed if isinstance(seed, (int, str)) and not isinstance(seed, bool) else None,
        "symbolic_inputs": symbols,
        "temporal_context": _canonical_context(temporal_context),
        "timestamp": timestamp,
    }
    return sha256_hex(canonical_json(payload))


def _empty_result(
    *,
    flags: list[str],
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
) -> ChronoOverlayResult:
    speculative = ChronoOverlaySpeculative(not_computable_flags=_unique_flags(flags))
    return _finalize(
        speculative,
        path=path,
        input_hash=input_hash,
        run_id=run_id,
        catalog_hash=catalog_hash,
        timestamp=timestamp,
        confidence=None,
    )


def _finalize(
    speculative: ChronoOverlaySpeculative,
    *,
    path: list[str],
    input_hash: str,
    run_id: object,
    catalog_hash: object,
    timestamp: str | None,
    confidence: float | None,
) -> ChronoOverlayResult:
    output_hash = sha256_hex(canonical_json(speculative.model_dump()))
    provenance = ChronoOverlayProvenance(
        run_id=run_id if isinstance(run_id, str) else None,
        input_hash=input_hash,
        output_hash=output_hash,
        catalog_hash=catalog_hash if isinstance(catalog_hash, str) else None,
        timestamp=timestamp,
        computation_path=list(path),
        confidence=confidence,
    )
    return ChronoOverlayResult(speculative=speculative, provenance=provenance)


# Isolation sentinels for tests / PACKET composers. Overlay never populates these.
FORBIDDEN_EVIDENCE_KEYS = ("observed", "inferred") + _OBSERVED_KEYS + _INFERRED_KEYS
