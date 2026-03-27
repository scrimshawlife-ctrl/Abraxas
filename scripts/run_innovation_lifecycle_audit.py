from __future__ import annotations

import json

from abx.innovation.lifecycleReports import build_innovation_lifecycle_audit_report


if __name__ == "__main__":
    print(json.dumps(build_innovation_lifecycle_audit_report(), indent=2, sort_keys=True))
