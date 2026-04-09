from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


ALLOWED_SIGNAL_SOURCES = ("mda", "ledger", "operator_snapshot", "validator")


@dataclass(frozen=True)
class OracleSignalInputEnvelopeV2:
    schema_id: str
    signal_sources: Sequence[str]
    payload: Mapping[str, Any]
    context: Mapping[str, Any]
    metadata: Mapping[str, Any]

    @staticmethod
    def from_dict(raw: Mapping[str, Any]) -> "OracleSignalInputEnvelopeV2":
        schema_id = str(raw.get("schema_id", ""))
        if schema_id != "OracleSignalInputEnvelope.v2":
            raise ValueError("schema_id must be OracleSignalInputEnvelope.v2")
        signal_sources = tuple(str(x) for x in (raw.get("signal_sources") or []))
        if not signal_sources:
            raise ValueError("signal_sources must be non-empty")
        for source in signal_sources:
            if source not in ALLOWED_SIGNAL_SOURCES:
                raise ValueError(f"unsupported signal_source: {source}")
        payload = raw.get("payload")
        context = raw.get("context")
        metadata = raw.get("metadata")
        if not isinstance(payload, Mapping):
            raise ValueError("payload must be object")
        if not isinstance(context, Mapping):
            raise ValueError("context must be object")
        if not isinstance(metadata, Mapping):
            raise ValueError("metadata must be object")
        return OracleSignalInputEnvelopeV2(
            schema_id=schema_id,
            signal_sources=signal_sources,
            payload=payload,
            context=context,
            metadata=metadata,
        )
