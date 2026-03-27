from __future__ import annotations

import json

from abx.productization.audienceReports import build_audience_legibility_audit_report


if __name__ == "__main__":
    print(json.dumps(build_audience_legibility_audit_report(), indent=2, sort_keys=True))
