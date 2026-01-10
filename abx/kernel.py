"""
Canonical kernel invocation spine (v0.1).
Deterministic, provenance-first, rune-mediated.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

from abx.purity import detector_purity_guard
from abx.runtime_events import emit as emit_event
from abx.schema_registry import payload_schema_for, result_schema_for
from abx.validate import validate_payload
from shared.aAlmanac import record_event
from shared.rune_ledger import record_invocation
from shared.policy import is_allowed, load_policy
from shared.stabilization import (
    advisory_cycles,
    bump_advisory_cycle,
    load_state,
    save_state,
)
from shared.governance import find_receipt
REGISTRY_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "registry",
    "abx_rune_registry.json",
)


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def _runtime_fingerprint() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
    }


def _hash_obj(obj: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True).encode("utf-8")
    ).hexdigest()


def load_registry() -> dict[str, Any]:
    with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def invoke(
    rune_id: str,
    payload: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Canonical kernel invocation.
    All cross-module execution must pass through here.
    """
    # Runtime telemetry: capture invocation start time
    start_ns = time.time_ns()
    event_base = {
        "rune_id": rune_id,
        "ts_ns": start_ns,
    }

    registry = load_registry()
    rune = next(
        (r for r in registry["runes"] if r["rune_id"] == rune_id),
        None,
    )
    if rune is None:
        raise ValueError(f"Unknown rune_id: {rune_id}")

    policy_doc = load_policy()
    if not is_allowed(policy_doc, rune_id):
        raise PermissionError(f"Rune denied by policy: {rune_id}")

    # Payload validation (inputs)
    spec = payload_schema_for(rune_id)
    if spec is not None:
        ok, errs = validate_payload(payload or {}, spec)
        if not ok:
            # Runtime telemetry: payload validation rejected
            emit_event({
                **event_base,
                "phase": "reject",
                "reason": "payload_validation_failed",
                "errors": errs,
            })
            raise ValueError(f"Payload validation failed for {rune_id}: {errs}")

    evidence_mode = rune.get("evidence_mode", "")
    is_detector = evidence_mode == "detector_only"
    is_actuator = evidence_mode == "ops_actuator"
    is_shadow_lane = evidence_mode == "shadow_lane"

    # P0 SECURITY: Shadow metrics access gate (ϟ₇ SSO rune required)
    if is_shadow_lane:
        # Check if caller has ϟ₇ SSO rune authorization
        caller_context = context or {}
        authorized_runes = caller_context.get("authorized_runes", [])

        if "ϟ₇" not in authorized_runes:
            raise PermissionError(
                f"Shadow lane access denied for {rune_id}. "
                "Requires ϟ₇ (Shadow Structural Observer) rune authorization. "
                "Shadow metrics are observe-only and must not be accessed directly."
            )

    stabilization = policy_doc.get("stabilization", {}) or {}
    required_cycles = int(stabilization.get("required_advisory_cycles", 3))
    state = load_state()

    if rune_id == "infra.self_heal":
        state = bump_advisory_cycle("infra.self_heal", state)
        save_state(state)

    if rune_id == "actuator.apply":
        cycles = advisory_cycles(state, "infra.self_heal")
        if cycles < required_cycles:
            raise PermissionError(
                "Stabilization gate: infra.self_heal "
                f"cycles={cycles} < required={required_cycles}"
            )

    if is_actuator:
        receipt_id = payload.get("governance_receipt_id")
        if not receipt_id:
            raise PermissionError(
                "Missing governance_receipt_id for actuator rune."
            )
        receipt = find_receipt(receipt_id)
        if not receipt:
            raise PermissionError(
                "Invalid governance_receipt_id (not found)."
            )
        if receipt.get("decision") != "APPROVE":
            raise PermissionError(
                "Governance decision is not APPROVE."
            )
        if receipt.get("action_rune_id") != rune_id:
            raise PermissionError(
                "Governance receipt rune mismatch."
            )

    seed = payload.get("seed")
    if seed is not None:
        # deterministic hook (explicit only)
        import random

        random.seed(seed)

    # Runtime telemetry: invocation started (after validation, before dispatch)
    emit_event({
        **event_base,
        "phase": "invoke_start",
    })

    # --- DISPATCH (v0.2: detector purity guarded) ---
    try:
        with detector_purity_guard(enabled=is_detector):
            if rune_id == "abx.doctor":
                from abx.doctor import run_doctor

                result = run_doctor(payload)
            elif rune_id == "compression.detect":
                from abraxas.compression.dispatch import detect_compression

                result = detect_compression(payload)
            elif rune_id == "infra.self_heal":
                from infra.self_heal_advisory import generate_plan

                result = generate_plan(payload)
            elif rune_id == "actuator.apply":
                from infra.actuator import apply

                result = apply(payload)
            else:
                raise NotImplementedError(
                    f"Rune wired but not yet routed: {rune_id}"
                )
    except Exception as dispatch_error:
        # Runtime telemetry: invocation failed
        end_ns = time.time_ns()
        emit_event({
            **event_base,
            "phase": "invoke_error",
            "duration_ns": end_ns - start_ns,
            "error_type": type(dispatch_error).__name__,
            "error": str(dispatch_error),
        })
        raise

    # Result validation (outputs) - strict for actuators, soft for detectors
    r_spec = result_schema_for(rune_id)
    if r_spec is not None:
        ok, errs = validate_payload(result or {}, r_spec)
        if not ok:
            if is_actuator:
                # Strict validation for actuators
                raise ValueError(f"Result validation failed for {rune_id}: {errs}")
            # Soft validation for detectors - log warning
            # (will be captured in provenance below)

    provenance_bundle = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "repo_commit": _git_commit(),
        "config_sha256": _hash_obj(payload),
        "runtime_fingerprint": _runtime_fingerprint(),
        "seed": seed,
    }

    # Add result validation warning for detectors
    if r_spec is not None and is_detector:
        ok, errs = validate_payload(result or {}, r_spec)
        if not ok:
            provenance_bundle["result_validation_warning"] = {
                "rune_id": rune_id,
                "errors": errs,
            }

    callsite: dict[str, Any] = {}
    try:
        stack = inspect.stack()
        for frame in stack:
            filename = frame.filename.replace("\\", "/")
            if not filename.endswith("/abx/kernel.py"):
                callsite = {
                    "file": filename,
                    "line": frame.lineno,
                    "function": frame.function,
                }
                break
    except Exception:
        callsite = {}

    _ = record_invocation(
        rune_id=rune_id,
        payload=payload,
        provenance_bundle=provenance_bundle,
        callsite=callsite,
    )

    _ = record_event(
        rune_id=rune_id,
        payload=payload,
        result=result,
        provenance_bundle=provenance_bundle,
    )

    # Runtime telemetry: invocation completed successfully
    end_ns = time.time_ns()
    emit_event({
        **event_base,
        "phase": "invoke_end",
        "duration_ns": end_ns - start_ns,
        "result_keys": sorted(list((result or {}).keys())),
    })

    return {
        "rune_id": rune_id,
        "result": result,
        "provenance_bundle": provenance_bundle,
        "context": context,
    }
