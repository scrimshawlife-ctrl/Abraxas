"""
Forecast Branch Ensemble (FBE) v0.1

Dynamic probabilistic forecasting with:
- Multiple branches per topic/horizon
- Deterministic probability updates via eligible influences
- Integrity-aware dampening (SSI-based)
- Full provenance via hash-chained ledgers

No ML. No randomness. Fully replayable.
"""

from abraxas.forecast.types import (
    Horizon,
    Branch,
    EnsembleState,
)
from abraxas.forecast.init import (
    default_ensemble_templates,
    init_ensemble_state,
)
from abraxas.forecast.update import (
    apply_influence_to_ensemble,
)
from abraxas.forecast.store import (
    load_ensemble,
    save_ensemble,
    append_branch_update_ledger,
)

__all__ = [
    # Types
    "Horizon",
    "Branch",
    "EnsembleState",
    # Initialization
    "default_ensemble_templates",
    "init_ensemble_state",
    # Updates
    "apply_influence_to_ensemble",
    # Storage
    "load_ensemble",
    "save_ensemble",
    "append_branch_update_ledger",
]
