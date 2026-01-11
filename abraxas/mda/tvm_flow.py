"""TVM framing + influence/synchronicity shadow flow for MDA."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability
from abraxas.schema.tvm import TVMVectorFrame, build_tvm_frame


def _build_ctx(run_id: str, subsystem_id: str, git_hash: str) -> RuneInvocationContext:
    return RuneInvocationContext(run_id=run_id, subsystem_id=subsystem_id, git_hash=git_hash)


def _build_run_id(payload: Dict[str, Any]) -> str:
    return f"mda_{sha256_hex(canonical_json(payload))[:12]}"


def frame_observations(
    observations: Optional[List[Dict[str, Any]]],
    *,
    run_id: str,
) -> List[TVMVectorFrame]:
    frames: List[TVMVectorFrame] = []
    for obs in observations or []:
        frames.append(build_tvm_frame(obs, run_id=run_id))
    return frames


def run_tvm_shadow_flow(
    *,
    observations: Optional[List[Dict[str, Any]]],
    env: Dict[str, Any],
    subsystem_id: str = "mda",
) -> Dict[str, Any]:
    run_id = _build_run_id(env)
    git_hash = str(env.get("git_hash") or "unknown")
    ctx = _build_ctx(run_id, subsystem_id, git_hash)

    frames = frame_observations(observations, run_id=run_id)
    frames_payload = [frame.model_dump() for frame in frames]

    influence = invoke_capability(
        "rune:influence_detect",
        {"frames": frames_payload},
        ctx=ctx,
    )
    weights = invoke_capability(
        "rune:influence_weight",
        {"ics_bundle": influence},
        ctx=ctx,
    )
    synchronicity = invoke_capability(
        "rune:synchronicity_map",
        {"frames": frames_payload},
        ctx=ctx,
    )
    cohesion = invoke_capability(
        "rune:cohesion_score",
        {"synchronicity_envelopes": synchronicity},
        ctx=ctx,
    )
    guard_causal = invoke_capability(
        "rune:no_causal_assert",
        {"payload": {"influence": influence, "synchronicity": synchronicity}},
        ctx=ctx,
    )
    guard_domain = invoke_capability(
        "rune:no_domain_prior",
        {"payload": {"frames": frames_payload, "env": env}},
        ctx=ctx,
    )

    shadow = {
        "tvm_v0_1": {
            "frames": frames_payload,
            "shadow_only": True,
        },
        "influence_v0_1": influence,
        "influence_weights_v0_1": weights,
        "synchronicity_v0_1": synchronicity,
        "cohesion_v0_1": cohesion,
        "guard_no_causal_assert": guard_causal,
        "guard_no_domain_prior": guard_domain,
    }

    return {
        "run_id": run_id,
        "tvm_frames": frames_payload,
        "shadow": shadow,
    }
