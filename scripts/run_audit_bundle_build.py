from __future__ import annotations

import json

from abx.closure.auditReports import build_audit_readiness_report


if __name__ == "__main__":
    print(json.dumps(build_audit_readiness_report(), indent=2, sort_keys=True))
