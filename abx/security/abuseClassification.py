from __future__ import annotations

from abx.security.abuseInventory import build_abuse_path_inventory


ABUSE_CLASSES = (
    "privilege_abuse",
    "override_abuse",
    "config_abuse",
    "interface_abuse",
    "stale_memory_abuse",
    "connector_adapter_abuse",
    "denial_degradation_abuse",
    "report_observability_abuse",
    "deployment_environment_abuse",
)


def classify_abuse_paths() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {k: [] for k in ABUSE_CLASSES}
    for record in build_abuse_path_inventory():
        key = record.abuse_class if record.abuse_class in out else "interface_abuse"
        out[key].append(record.abuse_id)
    return {k: sorted(v) for k, v in out.items()}


def detect_inconsistent_abuse_taxonomy() -> list[str]:
    return sorted({r.abuse_class for r in build_abuse_path_inventory() if r.abuse_class not in ABUSE_CLASSES})
