"""
Abraxas Runtime — Tick Orchestration

Canonical runtime layer that owns:
- ERS scheduler execution
- Artifact emission (TrendPack, ResultsPack, RunIndex)
- Structured tick output
- Pipeline bindings resolution
"""

from .tick import abraxas_tick
from .pipeline_bindings import PipelineBindings, PipelineFn, resolve_pipeline_bindings
from .results_pack import build_results_pack, make_result_ref

__all__ = [
    "abraxas_tick",
    "PipelineBindings",
    "PipelineFn",
    "resolve_pipeline_bindings",
    "build_results_pack",
    "make_result_ref",
]
