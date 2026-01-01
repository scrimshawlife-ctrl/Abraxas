# abraxas/alive/strain/v0_1.py
"""
Strain Heuristic v0.3 — Metric discovery engine.

Strain signals detect when the current metric set is insufficient
to explain the artifact's characteristics.

Signals:
A) Creative Capture Ignition: NCR≥0.65 AND GI≥0.65
   (living propaganda potential: creates while compressing)

B) Zombie Pressure: LFC≥0.70 AND GI≤0.30
   (high demand + no novelty = burnout engine)

C) Low Confidence Everywhere: avg_conf≤0.40
   (artifact too short/unclear; need more context)

D) Looped Self-Sealing: NCR≥0.60 AND RCF≥0.60 AND RFC≤0.35
   (high loop + high compression + low reality contact)

E) Testability Without Action: RFC≥0.70 AND GI≤0.35
   (testable claims with low conversion to outputs)
"""

from __future__ import annotations
from typing import Dict, Any, List
import uuid


def _get(signature: Dict[str, Any], metric_id: str) -> float:
    """Extract metric value from signature by ID."""
    for axis in ("influence", "vitality", "life_logistics"):
        for m in signature.get(axis, []) or []:
            if m.get("metric_id") == metric_id:
                return float(m.get("value", 0.0))
    return 0.0


def _conf(signature: Dict[str, Any]) -> float:
    """Compute average confidence across all present metrics."""
    vals = []
    for axis in ("influence", "vitality", "life_logistics"):
        for m in signature.get(axis, []) or []:
            vals.append(float(m.get("confidence", 0.0)))
    return sum(vals) / len(vals) if vals else 0.0


def compute_strain(signature: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute strain signals from ALIVE signature.

    Args:
        signature: Raw ALIVE metrics (influence, vitality, life_logistics)

    Returns:
        {
          "signals": [AliveStrainSignal...],
          "notes": string[]
        }
    """
    ncr = _get(signature, "IM.NCR")
    rcf = _get(signature, "IM.RCF")
    rfc = _get(signature, "IM.RFC")
    gi = _get(signature, "VM.GI")
    lfc = _get(signature, "LL.LFC")
    avg_conf = _conf(signature)

    signals: List[Dict[str, Any]] = []

    # Signal A: Creative Capture Ignition
    ignite = ncr * gi
    if ncr >= 0.65 and gi >= 0.65:
        signals.append(
            {
                "signal_id": str(uuid.uuid4()),
                "severity": "warning",
                "description": "Creative capture ignition: high generativity + high compression. Novelty may be channeling into a single frame.",
                "conflicting_metrics": ["IM.NCR", "VM.GI"],
                "unexplained_variance": max(0.0, ignite - 0.60),
                "suggested_new_dimension": {
                    "working_name": "Channel Lock",
                    "measures": "Degree to which generativity is permitted only inside a constrained frame.",
                    "candidate_axis": "cross_axis",
                    "candidate_buckets": [
                        "Narrative Artifacts",
                        "Counter-Narratives & Failures",
                        "Anomalies & Outliers",
                    ],
                },
            }
        )

    # Signal B: Zombie Pressure
    if lfc >= 0.70 and gi <= 0.30:
        signals.append(
            {
                "signal_id": str(uuid.uuid4()),
                "severity": "notice",
                "description": "Zombie pressure: high life-demand with low novelty. Predicts burnout and brittle adherence.",
                "conflicting_metrics": ["LL.LFC", "VM.GI"],
                "unexplained_variance": max(0.0, lfc - 0.70),
                "suggested_new_dimension": {
                    "working_name": "Renewal Capacity",
                    "measures": "Ability of the system to regenerate energy after demands.",
                    "candidate_axis": "vitality",
                    "candidate_buckets": [
                        "Friction Logs",
                        "Temporal Traces",
                        "First-Person Longitudinal Accounts",
                    ],
                },
            }
        )

    # Signal C: Low Confidence Everywhere
    if avg_conf <= 0.40:
        signals.append(
            {
                "signal_id": str(uuid.uuid4()),
                "severity": "info",
                "description": "Low confidence across metrics: artifact likely too short or context-thin; consider pairing or longer sample.",
                "unexplained_variance": 0.60 - avg_conf,
            }
        )

    # Signal D: Looped Self-Sealing
    if ncr >= 0.60 and rcf >= 0.60 and rfc <= 0.35:
        signals.append(
            {
                "signal_id": str(uuid.uuid4()),
                "severity": "warning",
                "description": "Looped self-sealing: high compression + high loop + low reality friction. Expect capture velocity without correction.",
                "conflicting_metrics": ["IM.NCR", "IM.RCF", "IM.RFC"],
                "unexplained_variance": max(0.0, (ncr + rcf) / 2.0 - rfc),
                "suggested_new_dimension": {
                    "working_name": "Moving Goalpost Pressure",
                    "measures": "Density of immunity clauses and goalpost shifts that block disconfirmation.",
                    "candidate_axis": "influence",
                    "candidate_buckets": [
                        "Immunity Clauses",
                        "Goalpost Shifts",
                        "Disconfirmation Blocks",
                    ],
                },
            }
        )

    # Signal E: Testability Without Action
    if rfc >= 0.70 and gi <= 0.35:
        signals.append(
            {
                "signal_id": str(uuid.uuid4()),
                "severity": "notice",
                "description": "Testability without action: high reality contact but low generativity. Claims may be true yet inert.",
                "conflicting_metrics": ["IM.RFC", "VM.GI"],
                "unexplained_variance": max(0.0, rfc - gi),
                "suggested_new_dimension": {
                    "working_name": "Actionability/Conversion Index",
                    "measures": "Degree to which testable claims produce concrete outputs or decisions.",
                    "candidate_axis": "vitality",
                    "candidate_buckets": [
                        "Decision Logs",
                        "Prototype Outputs",
                        "Operational Follow-Through",
                    ],
                },
            }
        )

    return {"signals": signals, "notes": []}
