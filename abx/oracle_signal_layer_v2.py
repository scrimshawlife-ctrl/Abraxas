from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from abraxas.oracle.runtime.service import run_oracle_signal_layer_v2_service
from abraxas.oracle.stability.invariance import run_invariance_v2
from abraxas.oracle.stability.digests import compute_digest_triplet
from abraxas.oracle.runtime.input_normalizer import normalize_input_v2
from abraxas.oracle.proof.validator_summary import build_validator_summary_v2


NOT_COMPUTABLE = "NOT_COMPUTABLE"


class OracleSignalLayerError(ValueError):
    """Compatibility error type for legacy callers."""


@dataclass(frozen=True)
class AdvisoryAdapter:
    adapter_id: str
    invoke: Callable[[Mapping[str, Any], Mapping[str, Any]], Mapping[str, Any]]


def _coerce_legacy_envelope(raw: Mapping[str, Any]) -> dict[str, Any]:
    if "schema_id" in raw and raw.get("schema_id") not in {"OracleSignalInputEnvelope.v2", ""} and "signal_sources" not in raw:
        raise OracleSignalLayerError("schema_id must be OracleSignalInputEnvelope.v2")
    if raw.get("schema_id") == "OracleSignalInputEnvelope.v2" and "signal_sources" in raw:
        return dict(raw)

    observations = list(raw.get("observations") or [])
    trend_inputs = list(raw.get("trend_inputs") or [])
    return {
        "schema_id": "OracleSignalInputEnvelope.v2",
        "signal_sources": ["mda"],
        "payload": {"observations": observations},
        "context": {"trend_inputs": trend_inputs},
        "metadata": {
            "run_id": str(raw.get("run_id", "oracle_signal_v2_run")),
            "lane": str(raw.get("lane", "shadow")),
            "tier": "advisory",
            "provenance": dict(raw.get("provenance") or {}),
        },
    }


def run_oracle_signal_layer_v2(
    envelope: Mapping[str, Any],
    *,
    adapters: Sequence[AdvisoryAdapter] | None = None,
) -> dict:
    coerced = _coerce_legacy_envelope(envelope)
    try:
        return run_oracle_signal_layer_v2_service(coerced)
    except Exception as exc:  # noqa: BLE001
        raise OracleSignalLayerError(str(exc)) from exc


def build_validator_summary(output: Mapping[str, Any]) -> dict:
    raw = {
        "schema_id": "OracleSignalInputEnvelope.v2",
        "signal_sources": ["mda"],
        "payload": {"observations": []},
        "context": {},
        "metadata": {"run_id": output.get("run_id", "unknown"), "lane": output.get("lane", "shadow"), "tier": "advisory"},
    }
    hashes = compute_digest_triplet(normalized=normalize_input_v2(raw), output=output)
    summary = build_validator_summary_v2(output=output, hashes=hashes, artifact_refs=[])
    summary["input_hash"] = hashes["input_hash"]
    summary["output_hash"] = hashes["full_hash"]
    return summary


def run_invariance(envelope: Mapping[str, Any], *, repeats: int = 12) -> dict:
    coerced = _coerce_legacy_envelope(envelope)
    report = run_invariance_v2(coerced, repeats=repeats)
    stable = report.get("status") == "PASS"
    report["input_invariant"] = stable
    report["output_invariant"] = stable
    report["authority_invariant"] = stable
    report["output_hash"] = report.get("full_hash")
    return report
