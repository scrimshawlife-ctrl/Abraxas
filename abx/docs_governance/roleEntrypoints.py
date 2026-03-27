from __future__ import annotations

from abx.docs_governance.roleInventory import build_onboarding_entries, build_role_entrypoints


def detect_role_terminology_drift() -> list[str]:
    known = {x.role_name for x in build_role_entrypoints()}
    drift = [x.role_name for x in build_onboarding_entries() if x.role_name not in known]
    return sorted(drift)
