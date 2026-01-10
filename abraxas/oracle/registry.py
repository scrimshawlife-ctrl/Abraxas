"""
Oracle Pipeline Registry — Canonical Pipeline Function Exports.

This module provides the single canonical entry point for Oracle pipeline functions.
The resolver in runtime/pipeline_bindings.py checks here first.

Exports:
    run_signal(ctx)   - Signal extraction phase
    run_compress(ctx) - Compression phase
    run_overlay(ctx)  - Overlay/forecast phase

All functions accept a context dict and return deterministic results.
"""

from __future__ import annotations

from typing import Any, Dict

from abraxas.oracle.v2.pipeline import OracleV2Pipeline, OracleSignal


# Singleton pipeline instance (lazy initialization)
_pipeline: OracleV2Pipeline | None = None


def _get_pipeline() -> OracleV2Pipeline:
    """Get or create the canonical OracleV2Pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = OracleV2Pipeline()
    return _pipeline


def run_signal(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Signal extraction phase.

    Extracts and normalizes signal from context observations.

    Args:
        ctx: Context dict with optional keys:
            - observations: List[str] - raw text observations
            - tokens: List[str] - pre-extracted tokens (if not present, extracts from observations)
            - domain: str - domain label (default: "general")
            - subdomain: Optional[str] - subdomain label
            - source_id: Optional[str] - source identifier
            - timestamp_utc: Optional[str] - timestamp (default: now)

    Returns:
        Dict with:
            - status: "ok" | "error"
            - signal: Serialized OracleSignal (if ok)
            - error: Error message (if error)
    """
    try:
        observations = ctx.get("observations", [])
        tokens = ctx.get("tokens", [])
        domain = ctx.get("domain", "general")
        subdomain = ctx.get("subdomain")
        source_id = ctx.get("source_id")

        # Extract tokens from observations if not provided
        if not tokens and observations:
            # Simple whitespace tokenization as fallback
            # In production, use a proper tokenizer
            tokens = []
            for obs in observations:
                if isinstance(obs, str):
                    tokens.extend(obs.lower().split())
            # Deduplicate while preserving order
            seen = set()
            unique_tokens = []
            for t in tokens:
                if t not in seen:
                    seen.add(t)
                    unique_tokens.append(t)
            tokens = unique_tokens[:100]  # Cap at 100 tokens

        # Generate timestamp if not provided
        from abraxas.core.provenance import Provenance
        timestamp_utc = ctx.get("timestamp_utc") or Provenance.now_iso_z()

        signal = OracleSignal(
            domain=domain,
            subdomain=subdomain,
            observations=observations,
            tokens=tokens,
            timestamp_utc=timestamp_utc,
            source_id=source_id,
            meta=ctx.get("meta", {}),
        )

        # Store signal in context for downstream phases
        ctx["_signal"] = signal

        return {
            "status": "ok",
            "signal": {
                "domain": signal.domain,
                "subdomain": signal.subdomain,
                "token_count": len(signal.tokens),
                "observation_count": len(signal.observations),
                "timestamp_utc": signal.timestamp_utc,
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def run_compress(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compression phase.

    Runs DCE compression on the signal, extracting lifecycle states,
    transparency scores, and affect direction.

    Args:
        ctx: Context dict with:
            - _signal: OracleSignal from run_signal phase
            - run_id: Optional[str] - run identifier for provenance

    Returns:
        Dict with:
            - status: "ok" | "error"
            - compression: Compression phase summary (if ok)
            - error: Error message (if error)
    """
    try:
        signal = ctx.get("_signal")
        if signal is None:
            # Attempt to reconstruct signal from context
            run_signal(ctx)
            signal = ctx.get("_signal")

        if signal is None:
            return {
                "status": "error",
                "error": "No signal available - run_signal must be called first",
            }

        pipeline = _get_pipeline()
        run_id = ctx.get("run_id", "tick")
        git_sha = ctx.get("git_sha")

        # Run compression phase
        compression = pipeline._compression_phase(signal, run_id, git_sha)

        # Store for downstream
        ctx["_compression"] = compression

        return {
            "status": "ok",
            "compression": {
                "domain": compression.domain,
                "version": compression.version,
                "token_count": len(compression.compressed_tokens),
                "lifecycle_states": compression.lifecycle_states,
                "domain_signals": list(compression.domain_signals),
                "transparency_score": compression.transparency_score,
                "affect_direction": compression.affect_direction,
                "provenance_hash": compression.provenance.inputs_hash,
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def run_overlay(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Overlay/Forecast phase.

    Runs lifecycle forecasting, resonance detection, and weather prediction.

    Args:
        ctx: Context dict with:
            - _compression: CompressionPhase from run_compress
            - run_id: Optional[str] - run identifier for provenance

    Returns:
        Dict with:
            - status: "ok" | "error"
            - forecast: Forecast phase summary (if ok)
            - error: Error message (if error)
    """
    try:
        compression = ctx.get("_compression")
        if compression is None:
            # Attempt to run compression first
            run_compress(ctx)
            compression = ctx.get("_compression")

        if compression is None:
            return {
                "status": "error",
                "error": "No compression available - run_compress must be called first",
            }

        pipeline = _get_pipeline()
        run_id = ctx.get("run_id", "tick")
        git_sha = ctx.get("git_sha")

        # Run forecast phase
        forecast = pipeline._forecast_phase(compression, run_id, git_sha)

        # Store for downstream (if narrative phase is needed later)
        ctx["_forecast"] = forecast

        return {
            "status": "ok",
            "forecast": {
                "phase_transitions": forecast.phase_transitions,
                "transition_count": len(forecast.phase_transitions),
                "resonance_score": forecast.resonance_score,
                "resonating_domains": list(forecast.resonating_domains),
                "weather_trajectory": forecast.weather_trajectory,
                "memetic_pressure": forecast.memetic_pressure,
                "drift_velocity": forecast.drift_velocity,
                "provenance_hash": forecast.provenance.inputs_hash,
            },
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


__all__ = ["run_signal", "run_compress", "run_overlay"]
