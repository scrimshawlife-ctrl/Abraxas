"""
Abraxas Runtime — Tick Orchestration

Canonical runtime layer that owns:
- ERS scheduler execution
- Artifact emission (TrendPack, ResultsPack, ViewPack, RunIndex)
- Structured tick output
- Pipeline bindings resolution
- Viz artifact resolution (event + result merging)
- Artifact retention and pruning
"""

from .tick import abraxas_tick
from .pipeline_bindings import PipelineBindings, PipelineFn, resolve_pipeline_bindings
from .results_pack import build_results_pack, make_result_ref
from .view_pack import build_view_pack
from .viz_resolve import (
    load_trendpack,
    load_resultspack,
    resolve_event_result,
    resolve_trendpack_events,
    get_event_result_by_task,
    clear_resultspack_cache,
)
from .retention import (
    ArtifactPruner,
    PruneReport,
    DEFAULT_POLICY,
)

__all__ = [
    # Tick orchestration
    "abraxas_tick",
    # Pipeline bindings
    "PipelineBindings",
    "PipelineFn",
    "resolve_pipeline_bindings",
    # Results pack
    "build_results_pack",
    "make_result_ref",
    # View pack
    "build_view_pack",
    # Viz resolution
    "load_trendpack",
    "load_resultspack",
    "resolve_event_result",
    "resolve_trendpack_events",
    "get_event_result_by_task",
    "clear_resultspack_cache",
    # Retention
    "ArtifactPruner",
    "PruneReport",
    "DEFAULT_POLICY",
]
