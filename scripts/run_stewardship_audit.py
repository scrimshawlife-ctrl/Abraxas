from __future__ import annotations

import json

from abx.meta.stewardshipReports import build_stewardship_audit_report


if __name__ == "__main__":
    print(json.dumps(build_stewardship_audit_report(), indent=2, sort_keys=True))
