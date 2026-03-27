from __future__ import annotations

from abx.security.securityInventory import build_security_surface_inventory


CRITICALITY = ("critical", "important_bounded", "auxiliary", "legacy_redundant_candidate")
DOMAINS = (
    "action_authorization",
    "integrity_verification",
    "secret_credential_boundary",
    "abuse_control",
    "operator_recovery",
)


def classify_security_surfaces() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in CRITICALITY}
    for record in build_security_surface_inventory():
        out[record.criticality].append(record.surface_id)
    return {k: sorted(v) for k, v in out.items()}


def classify_security_domains() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in DOMAINS}
    for record in build_security_surface_inventory():
        out[record.security_domain].append(record.surface_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_duplicate_security_vocabulary() -> list[str]:
    bad = sorted({r.criticality for r in build_security_surface_inventory() if r.criticality not in CRITICALITY})
    return bad
