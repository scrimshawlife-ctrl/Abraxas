from __future__ import annotations

from typing import Any, Dict, Optional

from aal_core.aalmanac.scoring import compute_drift_charge_from_signals


def compute_drift(entry: Dict[str, Any], *, prior_entry: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    signals = entry.get("signals", {}) or {}
    drift = entry.setdefault("drift", {})

    current_charge = compute_drift_charge_from_signals(signals)
    drift["drift_charge"] = current_charge
    if not prior_entry:
        drift["delta_from_prior"] = 0.0
        return entry

    prior_drift = prior_entry.get("drift", {}) or {}
    prior_charge = float(prior_drift.get("drift_charge", 0.0) or 0.0)
    drift["delta_from_prior"] = current_charge - prior_charge
    return entry
