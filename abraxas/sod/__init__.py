"""SOD (Second-Order Symbolic Dynamics): Narrative cascade and counter-narrative modeling.

Modules:
- NCP (Narrative Cascade Predictor)
- CNF (Counter-Narrative Forecaster)
- EFTE (Epistemic Fatigue Threshold Engine)
- SPM (Susceptibility Profile Mapper)
- RRM (Recovery & Re-Stabilization Model)

All modules emit deterministic scenario envelopes with falsifiers.
No simulation engine yet — v1.4 provides scaffold only.
"""

from abraxas.sod.models import ScenarioEnvelope, ScenarioPath, SODInput
from abraxas.sod.ncp import NarrativeCascadePredictor
from abraxas.sod.cnf import CounterNarrativeForecaster
from abraxas.sod.efte import EpistemicFatigueThresholdEngine
from abraxas.sod.spm import SusceptibilityProfileMapper
from abraxas.sod.rrm import RecoveryReStabilizationModel

__all__ = [
    "ScenarioEnvelope",
    "ScenarioPath",
    "SODInput",
    "NarrativeCascadePredictor",
    "CounterNarrativeForecaster",
    "EpistemicFatigueThresholdEngine",
    "SusceptibilityProfileMapper",
    "RecoveryReStabilizationModel",
]
