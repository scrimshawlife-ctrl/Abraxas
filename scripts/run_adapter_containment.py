#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.boundary.adapterContainment import build_adapter_containment_report
from abx.boundary.connectorClassification import connector_classification_report


def main() -> None:
    print(
        json.dumps(
            {
                "artifactType": "BoundaryAdapterAudit.v1",
                "artifactId": "boundary-adapter-audit",
                "connectorClassification": connector_classification_report(),
                "containment": build_adapter_containment_report(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
