from __future__ import annotations

import json

from abx.productization.packageReports import build_packaging_audit_report


if __name__ == "__main__":
    print(json.dumps(build_packaging_audit_report(), indent=2, sort_keys=True))
