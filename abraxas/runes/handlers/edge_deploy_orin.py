"""Kernel handler for edge.deploy_orin rune."""

from __future__ import annotations

from typing import Any, Dict

from shared.evidence import sha256_obj


def plan_edge_deploy(payload: Dict[str, Any]) -> Dict[str, Any]:
    target_profile = payload.get("target_profile")
    release_artifacts = payload.get("release_artifacts")
    config = payload.get("config") or {}

    missing = []
    if target_profile is None:
        missing.append("target_profile")
    if release_artifacts is None:
        missing.append("release_artifacts")
    if missing:
        return {
            "deploy_receipt": {},
            "rollback_point": {},
            "provenance_bundle": {
                "inputs_sha256": sha256_obj(payload),
                "handler": "edge.deploy_orin",
                "plan_only": True,
            },
            "not_computable": {
                "reason": "missing required inputs",
                "missing_inputs": missing,
                "provenance": {"inputs_sha256": sha256_obj(payload)},
            },
        }

    deploy_receipt = {
        "status": "plan_only",
        "target_profile": target_profile,
        "release_artifacts": release_artifacts,
        "notes": config.get("notes"),
    }

    rollback_point = {
        "strategy": "noop",
        "reason": "plan_only",
    }

    return {
        "deploy_receipt": deploy_receipt,
        "rollback_point": rollback_point,
        "provenance_bundle": {
            "inputs_sha256": sha256_obj(payload),
            "handler": "edge.deploy_orin",
        },
    }
