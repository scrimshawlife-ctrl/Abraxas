#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.deployment.deploymentReports import build_deployment_audit_report


if __name__ == "__main__":
    print(json.dumps(build_deployment_audit_report(), indent=2, sort_keys=True))
