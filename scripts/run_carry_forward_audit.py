#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.knowledge.carryForwardChecks import run_carry_forward_checks
from abx.knowledge.forgettingReports import build_forgetting_report


def main() -> None:
    print(
        json.dumps(
            {
                "artifactType": "CarryForwardAudit.v1",
                "artifactId": "carry-forward-audit",
                "carryForward": run_carry_forward_checks(),
                "forgetting": build_forgetting_report(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
