from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


DEFAULT_GATES: Dict[str, Any] = {
    "min_days_run": 30,
    "min_v1_pass_rate": 1.0,
    "max_drift_violations": 0,
    "max_evidence_overflow": 0.0,
    "min_ci_corr": 0.6,
    "max_interaction_noise": 0.35,
}


def _extract_evidence_metrics_from_checks(checks: Dict[str, Any]) -> Dict[str, Any] | None:
    """
    Additive internal channel: checks may include a special key "_evidence_metrics".
    We lift it into compliance.meta.evidence and remove it from checks so the
    compliance.checks payload stays clean.
    """
    if not isinstance(checks, dict):
        return None
    m = checks.pop("_evidence_metrics", None)
    if isinstance(m, dict) and m:
        return m
    return None


def compliance_status(checks: Dict[str, Any]) -> str:
    """
    Deterministic mapping:
      - RED: v1 regressions OR drift violations OR evidence overflow
      - YELLOW: v1 perfect but v2 tracking weak/noisy
      - GREEN: all good
    """
    if checks["v1_golden_pass_rate"] < 1.0:
        return "RED"
    if checks["drift_budget_violations"] > 0:
        return "RED"
    if checks["evidence_bundle_overflow_rate"] > 0.0:
        return "RED"

    # Marginal allowed only when v1 is perfect.
    if checks["ci_volatility_correlation"] < DEFAULT_GATES["min_ci_corr"]:
        return "YELLOW"
    if checks["interaction_noise_rate"] > DEFAULT_GATES["max_interaction_noise"]:
        return "YELLOW"

    return "GREEN"


def build_compliance_report(
    *,
    checks: Dict[str, Any],
    config_hash: str,
    date_iso: str | None = None,
    gates: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    # Extract evidence metrics if present (pops from checks)
    evm = _extract_evidence_metrics_from_checks(checks)

    g = dict(DEFAULT_GATES if gates is None else gates)
    dt = date_iso or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    status = compliance_status(checks)

    rep = {
        "date_iso": dt,
        "status": status,
        "checks": checks,
        "gates": g,
        "provenance": {"config_hash": config_hash},
    }

    # Optional extra debug payload (schema-tolerant if additionalProperties allowed;
    # validator does not forbid).
    if evm is not None:
        rep["meta"] = {"evidence": evm}

    return rep
