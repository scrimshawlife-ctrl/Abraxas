"""Oracle Pipeline v2

Unified Signal → Compression → Forecast → Narrative assembly.

Integrates:
- Domain Compression Engines (DCE) with lifecycle awareness
- Lifecycle forecasting via LifecycleEngine + TauCalculator
- Resonance detection across domains
- Memetic weather trajectory prediction
- Provenance bundles with SHA-256 tracking

Additive-only governance: compliance report + deterministic mode routing.
No mutation of v1 scoring outputs.
"""

from .pipeline import (
    CompressionPhase,
    ForecastPhase,
    NarrativePhase,
    OracleSignal,
    OracleV2Output,
    OracleV2Pipeline,
    create_oracle_v2_pipeline,
)

__all__ = [
    "OracleSignal",
    "CompressionPhase",
    "ForecastPhase",
    "NarrativePhase",
    "OracleV2Output",
    "OracleV2Pipeline",
    "create_oracle_v2_pipeline",
]
