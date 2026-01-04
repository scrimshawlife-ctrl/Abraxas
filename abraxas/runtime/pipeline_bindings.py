"""
Pipeline Bindings — Deterministic Resolver for Abraxas Oracle Pipeline.

Resolves the real Oracle pipeline functions (Signal → Compression → Overlay)
and shadow tasks from the repo. No mock data, no silent fallbacks.

If the repo doesn't expose the expected function names/paths, the resolver
hard-fails with a clear error listing what it tried.

This is runtime-only: no AAL-Viz coupling, no ERS coupling.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, List, Optional, Tuple


PipelineFn = Callable[[Dict[str, Any]], Any]


@dataclass(frozen=True)
class PipelineBindings:
    """
    Native Abraxas pipeline bindings resolved from the repo.

    These are *callables* that accept (context: dict) and return deterministic results.

    Attributes:
        run_signal: Signal extraction function (context) -> Any
        run_compress: Compression function (context) -> Any
        run_overlay: Overlay function (context) -> Any
        shadow_tasks: Dict mapping task name to callable (may be empty, not a placeholder)
        provenance: Dict with binding source info for auditability
    """

    run_signal: PipelineFn
    run_compress: PipelineFn
    run_overlay: PipelineFn
    shadow_tasks: Dict[str, PipelineFn]
    provenance: Dict[str, Any]


def _try_import_attr(module_path: str, attr: str) -> Optional[PipelineFn]:
    """
    Try to import a specific attribute from a module.

    Returns the callable if found, None otherwise.
    No exceptions raised - failures return None.
    """
    try:
        mod = import_module(module_path)
    except Exception:
        return None
    fn = getattr(mod, attr, None)
    if callable(fn):
        return fn
    return None


def resolve_pipeline_bindings() -> PipelineBindings:
    """
    Deterministically resolve the Abraxas Oracle pipeline functions from common repo locations.

    Resolution order is fixed (deterministic). First match wins.

    If not found, raises RuntimeError with an explicit tried list so wiring issues
    surface immediately.

    Returns:
        PipelineBindings with resolved callables and provenance metadata.

    Raises:
        RuntimeError: If any required pipeline function cannot be resolved.
    """
    tried: List[Tuple[str, str]] = []

    # Candidate locations (ordered, deterministic).
    # Canonical registry first, then fallback locations.
    # Add/remove candidates as repo evolves; ordering remains stable.
    signal_candidates = [
        ("abraxas.oracle.registry", "run_signal"),
        ("abraxas.oracle.signal", "run_signal"),
        ("abraxas.oracle.signal_layer", "run_signal"),
        ("abraxas.oracle.pipeline", "run_signal"),
        ("abraxas.oracle.run", "run_signal"),
        ("abraxas.engine.oracle", "run_signal"),
    ]
    compress_candidates = [
        ("abraxas.oracle.registry", "run_compress"),
        ("abraxas.oracle.compression", "run_compress"),
        ("abraxas.oracle.compress", "run_compress"),
        ("abraxas.oracle.pipeline", "run_compress"),
        ("abraxas.oracle.run", "run_compress"),
        ("abraxas.engine.oracle", "run_compress"),
    ]
    overlay_candidates = [
        ("abraxas.oracle.registry", "run_overlay"),
        ("abraxas.oracle.overlay", "run_overlay"),
        ("abraxas.oracle.overlays", "run_overlay"),
        ("abraxas.oracle.pipeline", "run_overlay"),
        ("abraxas.oracle.run", "run_overlay"),
        ("abraxas.engine.oracle", "run_overlay"),
    ]

    def first_found(
        cands: List[Tuple[str, str]], track: List[Tuple[str, str]]
    ) -> Tuple[Optional[PipelineFn], Optional[str]]:
        """Find first matching callable from candidate list, track what was tried."""
        for mp, attr in cands:
            track.append((mp, attr))
            fn = _try_import_attr(mp, attr)
            if fn is not None:
                return fn, f"{mp}:{attr}"
        return None, None

    run_signal, signal_source = first_found(signal_candidates, tried)
    run_compress, compress_source = first_found(compress_candidates, tried)
    run_overlay, overlay_source = first_found(overlay_candidates, tried)

    missing = []
    if run_signal is None:
        missing.append("run_signal")
    if run_compress is None:
        missing.append("run_compress")
    if run_overlay is None:
        missing.append("run_overlay")

    # Shadow tasks: try to discover a dictionary provider.
    # Absence is valid (not a placeholder) — shadow lane simply has no tasks.
    shadow_tasks: Dict[str, PipelineFn] = {}
    shadow_source: Optional[str] = None

    shadow_providers = [
        ("abraxas.detectors.shadow.registry", "get_shadow_tasks"),
        ("abraxas.detectors.shadow", "get_shadow_tasks"),
        ("abraxas.shadow.registry", "get_shadow_tasks"),
        ("abraxas.runtime.shadow_bindings", "get_shadow_tasks"),
    ]
    shadow_tried: List[Tuple[str, str]] = []
    for mp, attr in shadow_providers:
        shadow_tried.append((mp, attr))
        fn = _try_import_attr(mp, attr)
        if fn is not None:
            # get_shadow_tasks() returns dict[str, callable]
            # Pass empty context — registry lookup is context-independent
            out = fn({})
            if isinstance(out, dict):
                # Retain only callables, stable ordering applied later by tick
                shadow_tasks = {k: v for k, v in out.items() if callable(v)}
                shadow_source = f"{mp}:{attr}"
            break

    if missing:
        # Fail hard: no placeholders, no silent fallback.
        # Include tried paths to make wiring fast.
        tried_lines = "\n".join([f"  - {mp}:{attr}" for mp, attr in tried])
        shadow_lines = "\n".join([f"  - {mp}:{attr}" for mp, attr in shadow_tried])
        raise RuntimeError(
            "Abraxas pipeline bindings unresolved.\n"
            f"Missing: {', '.join(missing)}\n\n"
            "Tried (oracle pipeline):\n"
            f"{tried_lines}\n\n"
            "Tried (shadow providers):\n"
            f"{shadow_lines}\n\n"
            "To fix: ensure your repo exports run_signal, run_compress, run_overlay\n"
            "at one of the candidate paths above (preferably abraxas.oracle.registry)."
        )

    # Provenance metadata for auditability
    provenance = {
        "bindings": "PipelineBindings.v0",
        "oracle": {
            "signal": signal_source,
            "compress": compress_source,
            "overlay": overlay_source,
        },
        "shadow": {
            "provider": shadow_source,
            "task_count": len(shadow_tasks),
            "task_names": sorted(shadow_tasks.keys()),
        },
    }

    return PipelineBindings(
        run_signal=run_signal,
        run_compress=run_compress,
        run_overlay=run_overlay,
        shadow_tasks=shadow_tasks,
        provenance=provenance,
    )


__all__ = ["PipelineBindings", "PipelineFn", "resolve_pipeline_bindings"]
