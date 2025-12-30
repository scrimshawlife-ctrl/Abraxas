from __future__ import annotations

from typing import Any, Dict, List, Tuple


class V2ValidationError(ValueError):
    pass


def _fail(msg: str) -> None:
    raise V2ValidationError(msg)


def _is_num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _req(d: Dict[str, Any], key: str, ctx: str) -> Any:
    if key not in d:
        _fail(f"missing key: {ctx}.{key}")
    return d[key]


def _req_type(x: Any, t: type | Tuple[type, ...], ctx: str) -> Any:
    if not isinstance(x, t):
        _fail(f"type error at {ctx}: expected {t}, got {type(x)}")
    return x


def validate_compliance_report(rep: Dict[str, Any]) -> None:
    """
    Shape enforcement aligned to schema/v2/v2_compliance_report.v1.json.
    We enforce required keys + basic bounds.
    """
    _req_type(rep, dict, "compliance")
    date_iso = _req(rep, "date_iso", "compliance")
    _req_type(date_iso, str, "compliance.date_iso")

    status = _req(rep, "status", "compliance")
    _req_type(status, str, "compliance.status")
    if status not in ("GREEN", "YELLOW", "RED"):
        _fail(f"enum error at compliance.status: {status!r}")

    checks = _req(rep, "checks", "compliance")
    _req_type(checks, dict, "compliance.checks")
    for k in (
        "v1_golden_pass_rate",
        "drift_budget_violations",
        "evidence_bundle_overflow_rate",
        "ci_volatility_correlation",
        "interaction_noise_rate",
    ):
        _req(checks, k, "compliance.checks")

    v1 = checks["v1_golden_pass_rate"]
    if not _is_num(v1) or not (0.0 <= float(v1) <= 1.0):
        _fail("bounds error at compliance.checks.v1_golden_pass_rate")

    drift = checks["drift_budget_violations"]
    if not isinstance(drift, int) or drift < 0:
        _fail("bounds error at compliance.checks.drift_budget_violations")

    overflow = checks["evidence_bundle_overflow_rate"]
    if not _is_num(overflow) or not (0.0 <= float(overflow) <= 1.0):
        _fail("bounds error at compliance.checks.evidence_bundle_overflow_rate")

    ci_corr = checks["ci_volatility_correlation"]
    if not _is_num(ci_corr) or not (0.0 <= float(ci_corr) <= 1.0):
        _fail("bounds error at compliance.checks.ci_volatility_correlation")

    noise = checks["interaction_noise_rate"]
    if not _is_num(noise) or not (0.0 <= float(noise) <= 1.0):
        _fail("bounds error at compliance.checks.interaction_noise_rate")

    gates = _req(rep, "gates", "compliance")
    _req_type(gates, dict, "compliance.gates")
    for k in (
        "min_days_run",
        "min_v1_pass_rate",
        "max_drift_violations",
        "max_evidence_overflow",
        "min_ci_corr",
        "max_interaction_noise",
    ):
        _req(gates, k, "compliance.gates")

    prov = _req(rep, "provenance", "compliance")
    _req_type(prov, dict, "compliance.provenance")
    cfg = _req(prov, "config_hash", "compliance.provenance")
    _req_type(cfg, str, "compliance.provenance.config_hash")
    if len(cfg) < 16:
        _fail("bounds error at compliance.provenance.config_hash (minLength 16)")


def validate_mode_decision(md: Dict[str, Any]) -> None:
    """
    Shape enforcement aligned to schema/v2/v2_mode_router_output.v1.json
    plus required fingerprint.
    """
    _req_type(md, dict, "mode_decision")
    mode = _req(md, "mode", "mode_decision")
    _req_type(mode, str, "mode_decision.mode")
    if mode not in ("SNAPSHOT", "ANALYST", "RITUAL"):
        _fail(f"enum error at mode_decision.mode: {mode!r}")

    reasons = _req(md, "reasons", "mode_decision")
    _req_type(reasons, list, "mode_decision.reasons")
    if len(reasons) > 10:
        _fail("bounds error at mode_decision.reasons (maxItems 10)")
    for i, r in enumerate(reasons):
        if not isinstance(r, str) or len(r) > 64:
            _fail(f"type/bounds error at mode_decision.reasons[{i}]")

    tags = _req(md, "tags", "mode_decision")
    _req_type(tags, dict, "mode_decision.tags")
    state = _req(tags, "state", "mode_decision.tags")
    _req_type(state, str, "mode_decision.tags.state")
    if state != "INFERRED":
        _fail(f"enum error at mode_decision.tags.state: {state!r}")
    conf = _req(tags, "confidence", "mode_decision.tags")
    if not _is_num(conf) or not (0.0 <= float(conf) <= 1.0):
        _fail("bounds error at mode_decision.tags.confidence")

    prov = _req(md, "provenance", "mode_decision")
    _req_type(prov, dict, "mode_decision.provenance")
    cfg = _req(prov, "config_hash", "mode_decision.provenance")
    _req_type(cfg, str, "mode_decision.provenance.config_hash")
    if len(cfg) < 16:
        _fail("bounds error at mode_decision.provenance.config_hash (minLength 16)")

    fp = _req(md, "fingerprint", "mode_decision")
    _req_type(fp, str, "mode_decision.fingerprint")
    if len(fp) < 16:
        _fail("bounds error at mode_decision.fingerprint (minLength 16)")


def validate_v2_block(v2: Dict[str, Any]) -> None:
    """
    Validates the minimal v2 governance block:
      - mode
      - mode_decision (with fingerprint)
      - compliance report
    """
    _req_type(v2, dict, "v2")
    mode = _req(v2, "mode", "v2")
    _req_type(mode, str, "v2.mode")
    md = _req(v2, "mode_decision", "v2")
    validate_mode_decision(md)
    comp = _req(v2, "compliance", "v2")
    validate_compliance_report(comp)
    # lock: v2.mode must equal mode_decision.mode
    if mode != md.get("mode"):
        _fail(f"mode lock violated: v2.mode={mode!r} mode_decision.mode={md.get('mode')!r}")


def validate_envelope_v2(envelope: Dict[str, Any]) -> None:
    """
    Validates envelope["oracle_signal"]["v2"] exists and is valid.
    """
    _req_type(envelope, dict, "envelope")
    sig = _req(envelope, "oracle_signal", "envelope")
    _req_type(sig, dict, "envelope.oracle_signal")
    v2 = _req(sig, "v2", "envelope.oracle_signal")
    validate_v2_block(v2)
