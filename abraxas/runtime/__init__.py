"""
Abraxas Runtime — Tick Orchestration

Canonical runtime layer that owns:
- ERS scheduler execution
- Artifact emission (TrendPack, ResultsPack, ViewPack, RunIndex, RunHeader)
- Structured tick output
- Pipeline bindings resolution
- Viz artifact resolution (event + result merging)
- Artifact retention and pruning
- Policy provenance tracking
- Run-level provenance (RunHeader)
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
from .policy_ref import (
    policy_ref_for_retention,
    policy_ref_for_file,
    verify_policy_ref,
)
from .policy_snapshot import (
    ensure_policy_snapshot,
    policy_ref_from_snapshot,
    resolve_snapshot_path,
    load_policy_snapshot,
    verify_policy_snapshot,
)
from .run_header import (
    ensure_run_header,
    load_run_header,
    verify_run_header,
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
    # Policy ref
    "policy_ref_for_retention",
    "policy_ref_for_file",
    "verify_policy_ref",
    # Policy snapshot
    "ensure_policy_snapshot",
    "policy_ref_from_snapshot",
    "resolve_snapshot_path",
    "load_policy_snapshot",
    "verify_policy_snapshot",
    # Run header
    "ensure_run_header",
    "load_run_header",
    "verify_run_header",
]
