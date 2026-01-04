"""
Pipeline Bindings — Canonical Resolver for Abraxas Oracle Pipeline.

Single import path to canonical registries:
- Oracle stages: abraxas.oracle.registry
- Shadow tasks: abraxas.detectors.shadow.registry

No path-guessing. No discovery magic. One import, one contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict


PipelineFn = Callable[[Dict[str, Any]], Any]


@dataclass(frozen=True)
class PipelineBindings:
    """
    Native Abraxas pipeline bindings resolved from canonical registries.

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


def resolve_pipeline_bindings() -> PipelineBindings:
    """
    Canonical resolver — single import path to registries.

    Oracle stages: imported from abraxas.oracle.registry
    Shadow tasks: imported from abraxas.detectors.shadow.registry

    No path-guessing. No fallback candidates. If registries don't exist,
    import fails loudly.

    Returns:
        PipelineBindings with resolved callables and provenance metadata.

    Raises:
        ImportError: If canonical registries cannot be imported.
    """
    from abraxas.oracle import registry as oracle_registry
    from abraxas.detectors.shadow import registry as shadow_registry

    # Oracle stages — direct import from canonical registry
    run_signal = oracle_registry.run_signal
    run_compress = oracle_registry.run_compress
    run_overlay = oracle_registry.run_overlay

    # Shadow tasks — registry handles discovery from registry_impl
    shadow_tasks = shadow_registry.get_shadow_tasks({})

    # Provenance metadata for auditability
    provenance = {
        "bindings": "PipelineBindings.v1",
        "oracle": {
            "signal": "abraxas.oracle.registry:run_signal",
            "compress": "abraxas.oracle.registry:run_compress",
            "overlay": "abraxas.oracle.registry:run_overlay",
        },
        "shadow": {
            "provider": "abraxas.detectors.shadow.registry:get_shadow_tasks",
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
