"""Kernel handler for daemon.ingest rune."""

from __future__ import annotations

from typing import Any, Dict

from shared.evidence import sha256_obj


def ingest_daemon_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    source_config = payload.get("source_config")
    poll_interval = payload.get("poll_interval")
    config = payload.get("config") or {}

    missing = []
    if source_config is None:
        missing.append("source_config")
    if poll_interval is None:
        missing.append("poll_interval")
    if missing:
        return {
            "raw_events": {},
            "ingest_log": {},
            "provenance_bundle": {
                "inputs_sha256": sha256_obj(payload),
                "handler": "daemon.ingest",
                "plan_only": True,
            },
            "not_computable": {
                "reason": "missing required inputs",
                "missing_inputs": missing,
                "provenance": {"inputs_sha256": sha256_obj(payload)},
            },
        }

    plan = {
        "plan_only": True,
        "source_config": source_config,
        "poll_interval": poll_interval,
        "mode": config.get("mode", "plan"),
    }

    return {
        "raw_events": {},
        "ingest_log": {
            "status": "plan_only",
            "details": plan,
        },
        "provenance_bundle": {
            "inputs_sha256": sha256_obj(payload),
            "handler": "daemon.ingest",
        },
    }
