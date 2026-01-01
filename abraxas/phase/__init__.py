"""Phase Detection Engine

Cross-domain phase alignment detection and synchronicity mapping.

This is where Abraxas becomes predictive, not descriptive:
- Detects when domains enter the same lifecycle phase
- Maps synchronicity patterns (domain X → domain Y phase coupling)
- Detects drift-resonance coupling
- Provides early warning for phase transitions

Critical for multi-domain forecasting and cascade prediction.
"""

from .detector import (
    PhaseAlignment,
    PhaseAlignmentDetector,
    SynchronicityMap,
    SynchronicityPattern,
    create_phase_detector,
)
from .early_warning import (
    PhaseTransitionWarning,
    EarlyWarningSystem,
    create_early_warning_system,
)
from .coupling import (
    DriftResonanceCoupling,
    CouplingDetector,
    create_coupling_detector,
)

__all__ = [
    # Phase alignment detection
    "PhaseAlignment",
    "PhaseAlignmentDetector",
    "SynchronicityMap",
    "SynchronicityPattern",
    "create_phase_detector",
    # Early warning system
    "PhaseTransitionWarning",
    "EarlyWarningSystem",
    "create_early_warning_system",
    # Drift-resonance coupling
    "DriftResonanceCoupling",
    "CouplingDetector",
    "create_coupling_detector",
]
