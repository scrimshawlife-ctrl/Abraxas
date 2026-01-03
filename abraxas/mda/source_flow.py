"""SourceAtlas resolution + temporal normalization shadow flow for MDA."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.mda.domains import declared_sources_for_domains, list_mda_domains
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


def _build_run_id(payload: Dict[str, Any]) -> str:
    return f"mda_sources_{sha256_hex(canonical_json(payload))[:12]}"


def run_source_shadow_flow(*, env: Dict[str, Any], subsystem_id: str = "mda") -> Dict[str, Any]:
    run_id = _build_run_id(env)
    git_hash = str(env.get("git_hash") or "unknown")
    ctx = RuneInvocationContext(run_id=run_id, subsystem_id=subsystem_id, git_hash=git_hash)

    domains = list_mda_domains()
    source_ids = declared_sources_for_domains(domains)
    source_resolution = invoke_capability(
        "rune:source_resolve",
        {"source_ids": source_ids},
        ctx=ctx,
    )

    redundancy = invoke_capability(
        "rune:source_redundancy_check",
        {"sources": source_resolution.get("sources")},
        ctx=ctx,
    )

    temporal_norm = invoke_capability(
        "rune:temporal_normalize",
        {
            "timestamp": env.get("run_at") or env.get("timestamp") or "1970-01-01T00:00:00Z",
            "timezone": env.get("timezone") or "UTC",
            "window": env.get("window") or {},
            "calendars": env.get("calendars") or ["gregorian", "iso_week"],
        },
        ctx=ctx,
    )

    discover = invoke_capability(
        "rune:source_discover",
        {
            "residuals": env.get("residuals") or [],
            "anomalies": env.get("anomalies") or [],
            "convergence": env.get("convergence") or [],
            "silence": env.get("silence") or [],
        },
        ctx=ctx,
    )

    source_packets = env.get("source_packets") or []
    metrics = invoke_capability(
        "rune:metric_extract",
        {"packets": source_packets},
        ctx=ctx,
    )
    tvm_frames = invoke_capability(
        "rune:tvm_frame",
        {
            "metrics": metrics.get("metrics") or [],
            "window_start_utc": env.get("window_start_utc") or env.get("run_at") or "1970-01-01T00:00:00Z",
            "window_end_utc": env.get("window_end_utc") or env.get("run_at") or "1970-01-01T00:00:00Z",
        },
        ctx=ctx,
    )

    shadow_payload = {
        "source_resolution": source_resolution,
        "source_redundancy": redundancy,
        "temporal_normalization": temporal_norm,
        "source_discovery": discover,
        "metrics": metrics,
        "tvm_frames": tvm_frames,
        "domains": [domain.model_dump() for domain in domains],
    }

    seal = invoke_capability(
        "rune:provenance_seal",
        {"payload": shadow_payload},
        ctx=ctx,
    )

    shadow = {
        "sources_v0_1": shadow_payload,
        "provenance_seal": seal,
        "shadow_only": True,
    }

    return {
        "run_id": run_id,
        "shadow": shadow,
    }
