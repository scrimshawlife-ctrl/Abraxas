"""Abraxas Performance Tuning Plane v0.1.

Deterministic, evidence-based performance tuning with canary workflows
and rent gates.

Key components:
- PerfTuningIR: Declarative tuning configuration
- Optimizer: Evidence-based tuning proposal generation
- Apply: Atomic apply/rollback with ERS integration
- Gates: Rent payment verification before promotion
"""

from abraxas.tuning.perf_ir import PerfTuningIR, load_active_tuning_ir
from abraxas.tuning.objectives import compute_objective, TuningObjective
from abraxas.tuning.optimizer import propose_tuning
from abraxas.tuning.apply import validate_ir, apply_ir_atomically, rollback_to_previous
from abraxas.tuning.gates import check_rent_gates, RentGateVerdict

__all__ = [
    "PerfTuningIR",
    "load_active_tuning_ir",
    "TuningObjective",
    "compute_objective",
    "propose_tuning",
    "validate_ir",
    "apply_ir_atomically",
    "rollback_to_previous",
    "check_rent_gates",
    "RentGateVerdict",
]
