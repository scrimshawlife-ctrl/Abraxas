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
        ConnectorCapabilityRecord(
            connector_id="connector.worldbank_region_v2",
            role="translation",
            allowed_actions=["fetch", "shape"],
            disallowed_actions=["policy_decision", "trust_escalation", "authoritative_mutation"],
        ),
        ConnectorCapabilityRecord(
            connector_id="connector.exchangerate_open_v6",
            role="translation",
            allowed_actions=["fetch", "shape"],
            disallowed_actions=["policy_decision", "trust_escalation", "authoritative_mutation"],
        ),
        ConnectorCapabilityRecord(
            connector_id="connector.usgs_earthquake_fdsn",
            role="translation",
            allowed_actions=["fetch", "shape"],
            disallowed_actions=["policy_decision", "trust_escalation", "authoritative_mutation"],
        ),
        ConnectorCapabilityRecord(
            connector_id="connector.us_federal_register",
            role="translation",
            allowed_actions=["fetch", "shape"],
            disallowed_actions=["policy_decision", "trust_escalation", "authoritative_mutation"],
        ),
        ConnectorCapabilityRecord(
            connector_id="connector.restcountries_v3",
            role="translation",
            allowed_actions=["fetch", "shape"],
            disallowed_actions=["policy_decision", "trust_escalation", "authoritative_mutation"],
        ),
    ]
    return sorted(rows, key=lambda x: x.connector_id)
