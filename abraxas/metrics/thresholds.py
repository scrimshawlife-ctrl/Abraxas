"""
Deterministic thresholds for metric evaluation and promotion.

All thresholds are global constants to ensure reproducibility.
Modifications require ledger documentation.
"""

from __future__ import annotations

# Redundancy detection thresholds
MAX_REDUNDANCY_CORR = 0.85
"""Maximum correlation with existing metrics before rejection (Pearson r)"""

MIN_REDUNDANCY_EUCLIDEAN_DIST = 0.15
"""Minimum normalized Euclidean distance from existing metrics"""

# Forecast improvement thresholds
MIN_FORECAST_ERROR_DELTA = 0.02
"""Minimum improvement in forecast error (MAE or RMSE reduction)"""

MIN_BRIER_DELTA = 0.01
"""Minimum improvement in Brier score for probabilistic forecasts"""

MIN_MISINFO_AUC_DELTA = 0.03
"""Minimum improvement in AUC for misinformation detection tasks"""

# Ablation thresholds
MIN_ABLATION_DAMAGE = 0.05
"""Minimum performance degradation when metric is removed (proves necessity)"""

MAX_ABLATION_DAMAGE = 0.30
"""Maximum tolerable damage during ablation (safety limit)"""

# Stabilization thresholds
MIN_STABILITY_CYCLES = 5
"""Minimum number of consecutive stable evaluation cycles required"""

MAX_STABILITY_VARIANCE = 0.10
"""Maximum coefficient of variation across stability cycles"""

# Drift detection thresholds
DRIFT_PERTURBATION_LEVELS = [0.05, 0.10, 0.20]
"""Perturbation magnitudes for synthetic drift testing (as fraction of std dev)"""

MIN_DRIFT_SENSITIVITY = 0.60
"""Minimum detection rate for synthetic drift events"""

# Temporal decay thresholds
MIN_TEMPORAL_HALF_LIFE_CYCLES = 10
"""Minimum half-life in simulation cycles before metric is flagged as unstable"""

# Evidence bundle requirements
MIN_EVIDENCE_SAMPLES = 100
"""Minimum ledger entries required for metric evaluation"""

MIN_EVIDENCE_WINDOW_DAYS = 7
"""Minimum time span for evidence collection (days)"""

# Scoring thresholds for promotion gates
MIN_COMPOSITE_SCORE = 0.70
"""Minimum composite score across all evaluation dimensions"""

PROMOTION_REQUIRED_GATES = [
    "non_redundant",
    "forecast_lift",
    "ablation_proof",
    "stability_verified",
    "drift_robust",
]
"""All gates that must pass for metric to be promoted"""
