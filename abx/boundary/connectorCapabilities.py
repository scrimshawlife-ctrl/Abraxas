from __future__ import annotations

from abx.boundary.types import ConnectorCapabilityRecord


def build_connector_capabilities() -> list[ConnectorCapabilityRecord]:
    rows = [
        ConnectorCapabilityRecord(
            connector_id="connector.http_snapshot",
            role="translation",
            allowed_actions=["fetch", "shape"],
            disallowed_actions=["policy_decision", "authoritative_mutation"],
        ),
        ConnectorCapabilityRecord(
            connector_id="connector.noaa_swpc_kp",
            role="translation",
            allowed_actions=["fetch", "normalize"],
            disallowed_actions=["trust_escalation", "runtime_decision"],
        ),
    ]
    return sorted(rows, key=lambda x: x.connector_id)
