from __future__ import annotations

from abx.boundary.connectorCapabilities import build_connector_capabilities


def connector_classification_report() -> dict[str, object]:
    rows = [x.__dict__ for x in build_connector_capabilities()]
    return {
        "artifactType": "ConnectorClassificationReport.v1",
        "artifactId": "connector-classification-report",
        "connectors": rows,
    }
