"""
Ensemble Initialization

Provides deterministic templates and initialization for forecast ensembles.
No ML, no randomness—just conservative defaults.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from abraxas.forecast.types import Branch, EnsembleState, Horizon


def generate_ensemble_id(
    topic_key: str, horizon: Horizon, segment: str, narrative: str
) -> str:
    """Generate deterministic ensemble ID from components."""
    components = f"{topic_key}|{horizon.value}|{segment}|{narrative}"
    hash_hex = hashlib.sha256(components.encode()).hexdigest()
    return f"ensemble_{topic_key}_{horizon.value}_{segment}_{narrative}_{hash_hex[:8]}"


def generate_branch_id(ensemble_id: str, label: str) -> str:
    """Generate deterministic branch ID."""
    components = f"{ensemble_id}|{label}"
    hash_hex = hashlib.sha256(components.encode()).hexdigest()
    return f"branch_{label}_{hash_hex[:8]}"


def default_ensemble_templates() -> Dict[str, Dict]:
    """
    Provide deterministic templates for canonical topics.

    Returns dict mapping topic_key to template config.
    """
    return {
        "deepfake_pollution": {
            "description": "Deepfake content saturation and detection failure",
            "branches": {
                "conservative": {
                    "p": 0.35,
                    "description": "Current detection methods hold; deepfakes remain identifiable",
                    "triggers": [
                        {"kind": "index_threshold", "params": {"index": "SSI", "lte": 0.4}}
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.5},
                },
                "base": {
                    "p": 0.40,
                    "description": "Moderate increase in unverified content; detection strained",
                    "triggers": [
                        {
                            "kind": "index_threshold",
                            "params": {"index": "SSI", "gte": 0.4, "lte": 0.6},
                        }
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.6},
                },
                "shock": {
                    "p": 0.25,
                    "description": "Detection overwhelmed; trust crisis in visual media",
                    "triggers": [
                        {"kind": "index_threshold", "params": {"index": "SSI", "gte": 0.7}},
                        {"kind": "term_seen", "params": {"term": "deepfake", "min_count": 10}},
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.8},
                },
            },
        },
        "propaganda_pressure": {
            "description": "Coordinated influence campaign intensity",
            "branches": {
                "conservative": {
                    "p": 0.40,
                    "description": "Low-level background noise; no coordinated campaigns",
                    "triggers": [
                        {
                            "kind": "integrity_vector",
                            "params": {"vector": "Coordinated Inauthentic Behavior", "min_score": 0.3},
                        }
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.4},
                },
                "sustained": {
                    "p": 0.35,
                    "description": "Sustained propaganda campaign across multiple channels",
                    "triggers": [
                        {
                            "kind": "integrity_vector",
                            "params": {"vector": "Coordinated Inauthentic Behavior", "min_score": 0.6},
                        },
                        {"kind": "term_seen", "params": {"term": "propaganda", "min_count": 5}},
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.7},
                },
                "crisis": {
                    "p": 0.25,
                    "description": "Intense multi-platform campaign; institutional response",
                    "triggers": [
                        {
                            "kind": "integrity_vector",
                            "params": {"vector": "Coordinated Inauthentic Behavior", "min_score": 0.8},
                        },
                        {"kind": "index_threshold", "params": {"index": "SSI", "gte": 0.75}},
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.9},
                },
            },
        },
        "integrity_collapse": {
            "description": "Systemic failure of content verification mechanisms",
            "branches": {
                "conservative": {
                    "p": 0.50,
                    "description": "Current verification methods adequate",
                    "triggers": [
                        {"kind": "index_threshold", "params": {"index": "SSI", "lte": 0.5}}
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.3},
                },
                "degraded": {
                    "p": 0.30,
                    "description": "Partial verification failure; trust declining",
                    "triggers": [
                        {"kind": "index_threshold", "params": {"index": "SSI", "gte": 0.5, "lte": 0.7}}
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.6},
                },
                "collapsed": {
                    "p": 0.20,
                    "description": "Widespread verification failure; content provenance lost",
                    "triggers": [
                        {"kind": "index_threshold", "params": {"index": "SSI", "gte": 0.8}},
                        {
                            "kind": "integrity_vector",
                            "params": {"vector": "Authority Deepfake", "min_score": 0.7},
                        },
                    ],
                    "manipulation_exposure": {"SSI_sensitivity": 0.9},
                },
            },
        },
    }


def init_ensemble_state(
    topic_key: str,
    horizon: Horizon,
    segment: str = "core",
    narrative: str = "N1_primary",
    now_ts: Optional[datetime] = None,
    ctx_snapshots: Optional[Dict[str, Any]] = None,
) -> EnsembleState:
    """
    Initialize ensemble state from template.

    Args:
        topic_key: Topic identifier
        horizon: Forecast horizon
        segment: "core" or "peripheral"
        narrative: "N1_primary" or "N2_counter"
        now_ts: Timestamp for initialization
        ctx_snapshots: Optional context snapshots (MW/τ/Integrity) for prior adjustment

    Returns:
        EnsembleState with initialized branches
    """
    if now_ts is None:
        now_ts = datetime.now(timezone.utc)

    if ctx_snapshots is None:
        ctx_snapshots = {}

    # Generate ensemble ID
    ensemble_id = generate_ensemble_id(topic_key, horizon, segment, narrative)

    # Get template
    templates = default_ensemble_templates()
    if topic_key not in templates:
        raise ValueError(f"No template for topic_key: {topic_key}")

    template = templates[topic_key]

    # Build branches
    branches = []
    tau_window_hours = horizon.to_hours()

    for label, branch_config in template["branches"].items():
        branch_id = generate_branch_id(ensemble_id, label)

        # Apply small deterministic adjustments from context (conservative)
        p_base = branch_config["p"]
        p_adjusted = _adjust_prior_from_context(
            p_base, label, ctx_snapshots, max_delta=0.05
        )

        # Confidence bands (start conservative)
        band_width = 0.10
        p_min = max(0, p_adjusted - band_width)
        p_max = min(1, p_adjusted + band_width)

        branch = Branch(
            branch_id=branch_id,
            horizon=horizon,
            segment=segment,
            narrative=narrative,
            label=label,
            description=branch_config["description"],
            p=p_adjusted,
            p_min=p_min,
            p_max=p_max,
            tau_window_hours=tau_window_hours,
            triggers=branch_config.get("triggers", []),
            falsifiers=branch_config.get("falsifiers", []),
            manipulation_exposure=branch_config.get("manipulation_exposure", {}),
            provenance={
                "template": topic_key,
                "initialized_at": now_ts.isoformat(),
                "ctx_snapshots_used": list(ctx_snapshots.keys()),
            },
            created_at=now_ts,
            last_updated_at=now_ts,
        )

        branches.append(branch)

    # Renormalize to ensure sum(p) = 1.0
    total_p = sum(b.p for b in branches)
    for branch in branches:
        branch.p = branch.p / total_p

    ensemble = EnsembleState(
        ensemble_id=ensemble_id,
        topic_key=topic_key,
        horizon=horizon,
        segment=segment,
        narrative=narrative,
        branches=branches,
        last_updated_ts=now_ts,
        provenance={
            "template": topic_key,
            "initialized_at": now_ts.isoformat(),
            "branch_count": len(branches),
        },
    )

    return ensemble


def _adjust_prior_from_context(
    p_base: float,
    label: str,
    ctx_snapshots: Dict[str, Any],
    max_delta: float = 0.05,
) -> float:
    """
    Apply small deterministic adjustments to prior based on context.

    Conservative: Only small shifts, capped by max_delta.
    """
    delta = 0.0

    # Example: If SSI is high and label is "shock", nudge up slightly
    if "integrity" in ctx_snapshots:
        ssi = ctx_snapshots["integrity"].get("SSI", 0.5)
        if ssi > 0.6 and label in ["shock", "crisis", "collapsed"]:
            delta += 0.02
        elif ssi < 0.4 and label == "conservative":
            delta += 0.02

    # Cap delta
    delta = max(-max_delta, min(max_delta, delta))

    return max(0, min(1, p_base + delta))
