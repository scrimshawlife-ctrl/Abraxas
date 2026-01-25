"""Kernel handler for ser.run rune."""

from __future__ import annotations

from typing import Any, Dict

from shared.evidence import sha256_obj
from abraxas.scenario.runner import run_scenarios
from abraxas.sod.runner import run_sod_bundle


def _build_run_id(payload: Dict[str, Any]) -> str:
    return f"ser-{sha256_obj(payload)[:12]}"


def run_scenario_envelope(payload: Dict[str, Any]) -> Dict[str, Any]:
    priors = payload.get("priors")
    signals = payload.get("signals")
    config = payload.get("config") or {}

    missing = []
    if priors is None:
        missing.append("priors")
    if signals is None:
        missing.append("signals")
    if missing:
        return {
            "envelope": {},
            "cascade_sheet": {},
            "contamination_advisory": {},
            "provenance_bundle": {
                "inputs_sha256": sha256_obj(payload),
                "handler": "ser.run",
                "plan_only": True,
            },
            "not_computable": {
                "reason": "missing required inputs",
                "missing_inputs": missing,
                "provenance": {"inputs_sha256": sha256_obj(payload)},
            },
        }

    run_id = config.get("run_id") or signals.get("run_id") or _build_run_id(payload)
    timestamp = (
        config.get("timestamp_utc")
        or signals.get("timestamp_utc")
        or "1970-01-01T00:00:00Z"
    )

    context: Dict[str, Any] = {
        "run_id": run_id,
        "timestamp": timestamp,
        "weather": signals.get("weather"),
        "dm_snapshot": signals.get("dm_snapshot"),
        "almanac_snapshot": signals.get("almanac_snapshot"),
        "notes": signals.get("notes"),
        "source_count": signals.get("source_count", 0),
    }

    result = run_scenarios(priors, run_sod_bundle, context)
    envelope = result.to_dict()

    cascade_sheet = {
        "envelope_count": len(envelope.get("envelopes", [])),
        "confidence_levels": sorted(
            {env.get("confidence") for env in envelope.get("envelopes", [])}
        ),
    }

    contamination_advisory = {}
    if any(env.get("confidence") == "LOW" for env in envelope.get("envelopes", [])):
        contamination_advisory = {
            "risk_level": "LOW_CONFIDENCE",
            "note": "One or more envelopes returned LOW confidence.",
        }

    return {
        "envelope": envelope,
        "cascade_sheet": cascade_sheet,
        "contamination_advisory": contamination_advisory,
        "provenance_bundle": {
            "inputs_sha256": sha256_obj(payload),
            "handler": "ser.run",
        },
    }
