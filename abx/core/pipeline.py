"""Abraxas pipeline - Oracle execution with ABX-Runes integration.

Integrates ϟ₄ (SDS), ϟ₅ (IPL), ϟ₆ (ADD) into oracle execution path.
All outputs are provenance-stamped with rune metadata.
"""

from __future__ import annotations
from typing import Any, Dict

from abx.oracle.rune_gate import compute_gate, enforce_depth, schedule_insight_window
from abx.oracle.drift import drift_check, append_drift_log
from abx.oracle.provenance import stamp
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.core.oracle_runner import run_oracle as run_kernel_oracle
from abraxas.io.config import UserConfig, OverlaysConfig


def run_oracle(
    input_obj: Dict[str, Any],
    state_vector: Dict[str, float] | None = None,
    context: Dict[str, Any] | None = None,
    requested_depth: str = "deep",
    anchor: str | None = None,
    outputs_history: list[str] | None = None,
    rune_ctx: RuneInvocationContext | dict | None = None,
    strict_execution: bool = True,
) -> Dict[str, Any]:
    """Run Abraxas Oracle pipeline with ABX-Runes integration.

    Execution order:
    A) Compute SDS gate (ϟ₄)
    B) Enforce depth based on gate state
    C) Generate oracle output
    D) If CLOSED, return grounding output
    E) Schedule IPL windows (ϟ₅) if gate is OPEN
    F) Check anchor drift (ϟ₆)
    G) Stamp output with rune provenance
    H) Append drift log entry

    Args:
        input_obj: Input vector for oracle (required)
        state_vector: Receiver state dimensions (defaults to 0.5 for all dims)
        context: Contextual metadata (defaults to empty dict)
        requested_depth: Desired depth level ("grounding" | "shallow" | "deep")
        anchor: Semantic anchor for drift detection (defaults to input intent)
        outputs_history: Recent oracle outputs for drift analysis (defaults to empty)

    Returns:
        Oracle output with ABX-Runes provenance embedded in "abx_runes" key
    """
    # A) Initialize defaults deterministically
    if state_vector is None:
        state_vector = {}  # compute_gate will apply defaults
    if context is None:
        context = {}
    if outputs_history is None:
        outputs_history = []
    if anchor is None:
        # Use input intent as anchor fallback
        anchor = input_obj.get("intent", "oracle")

    if rune_ctx is None:
        run_id = input_obj.get("run_id") or context.get("run_id") or "ORACLE_RUN"
        git_hash = input_obj.get("git_hash") or context.get("git_hash") or "unknown"
        rune_ctx = RuneInvocationContext(
            run_id=str(run_id),
            subsystem_id="abx.core.pipeline",
            git_hash=str(git_hash),
        )

    # B) Compute SDS gate (ϟ₄)
    gate_bundle = compute_gate(
        state_vector=state_vector,
        context=context,
        interaction_kind="oracle",
        ctx=rune_ctx,
        strict_execution=strict_execution,
    )

    # C) Enforce depth based on gate state
    effective_depth = enforce_depth(gate_bundle, requested_depth)

    # D) Generate oracle output based on effective depth
    if effective_depth == "grounding":
        # Return minimal grounding output when gate is CLOSED
        output = {
            "oracle_vector": input_obj,
            "depth": "grounding",
            "message": "Receiver state not aligned; grounding response only.",
            "semiotic_weather": {"status": "grounded"},
            "outputs": [],
        }
    else:
        user_payload = input_obj.get("user") or context.get("user") or {}
        overlays_payload = input_obj.get("overlays") or context.get("overlays") or {}
        day = input_obj.get("day") or context.get("day") or "1970-01-01"
        checkin = input_obj.get("checkin") or context.get("checkin")
        timestamp_utc = input_obj.get("timestamp_utc") or context.get("timestamp_utc") or "1970-01-01T00:00:00Z"

        user_config = (
            UserConfig.from_dict(user_payload)
            if isinstance(user_payload, dict)
            else UserConfig.default()
        )
        overlays_config = (
            OverlaysConfig.from_dict(overlays_payload)
            if isinstance(overlays_payload, dict)
            else OverlaysConfig.default()
        )

        oracle_outputs = run_kernel_oracle(user_config, overlays_config, day, checkin=checkin)
        readout = dict(oracle_outputs.readout)
        provenance = dict(readout.get("provenance", {}) or {})
        if provenance:
            provenance["timestamp_utc"] = timestamp_utc
            readout["provenance"] = provenance

        output = {
            "oracle_vector": input_obj,
            "depth": effective_depth,
            "semiotic_weather": readout.get("runic_weather", {}),
            "outputs": [readout],
        }

    # E) Schedule IPL windows (ϟ₅) if gate is OPEN
    # Extract phase_series from oracle if available (stub uses None)
    phase_series = output.get("phase_series", None)
    ipl_schedule = schedule_insight_window(
        phase_series=phase_series,
        gate_bundle=gate_bundle,
        ctx=rune_ctx,
        strict_execution=strict_execution,
    )

    # F) Check anchor drift (ϟ₆)
    drift_bundle = drift_check(
        anchor=anchor,
        outputs_history=outputs_history,
        window=20,
        ctx=rune_ctx,
        strict_execution=strict_execution,
    )

    # If auto_recenter is True, annotate output (do NOT mutate history)
    if drift_bundle.get("auto_recenter"):
        output["recenter_suggested"] = True

    # G) Stamp output with rune provenance
    runes_used = ["ϟ₁", "ϟ₂", "ϟ₄", "ϟ₅", "ϟ₆"]
    extras = {
        "susceptibility_score": gate_bundle["susceptibility_score"],
        "depth_applied": effective_depth,
        "ipl": ipl_schedule,
        "drift": drift_bundle,
    }

    stamp(
        output=output,
        runes_used=runes_used,
        gate_state=gate_bundle["gate_state"],
        extras=extras
    )

    # H) Append drift log entry
    from abx.oracle.provenance import load_manifest_sha256
    append_drift_log(
        anchor=anchor,
        drift_bundle=drift_bundle,
        gate_state=gate_bundle["gate_state"],
        runes_used=runes_used,
        manifest_sha256=load_manifest_sha256()
    )

    return output
