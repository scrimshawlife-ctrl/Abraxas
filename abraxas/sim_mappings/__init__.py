"""Simulation Mapping Layer (SML): Academic model parameter bridge to Abraxas knobs.

Maps simulation model parameters (β, γ, influence weights, etc.) to Abraxas operational
metrics (MRI, IRI, τ) for future integration of academic models.
"""

from abraxas.sim_mappings.types import (
    PaperRef,
    ModelFamily,
    ModelParam,
    KnobVector,
    MappingResult,
)
from abraxas.sim_mappings.mapper import map_params_to_knobs, map_paper_model

__all__ = [
    "PaperRef",
    "ModelFamily",
    "ModelParam",
    "KnobVector",
    "MappingResult",
    "map_params_to_knobs",
    "map_paper_model",
]
