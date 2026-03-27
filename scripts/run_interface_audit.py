#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.boundary.interfaceClassification import classify_interface_surfaces, detect_redundant_entrypoints
from abx.boundary.interfaceContracts import build_interface_contracts
from abx.boundary.interfaceOwnership import interface_ownership_report


def main() -> None:
    print(
        json.dumps(
            {
                "artifactType": "BoundaryInterfaceAudit.v1",
                "artifactId": "boundary-interface-audit",
                "contracts": [x.__dict__ for x in build_interface_contracts()],
                "classification": classify_interface_surfaces(),
                "ownership": interface_ownership_report(),
                "redundantEntrypoints": detect_redundant_entrypoints(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
