from __future__ import annotations

import json

from abx.productization.outputReports import build_output_boundedness_audit_report


if __name__ == "__main__":
    print(json.dumps(build_output_boundedness_audit_report(), indent=2, sort_keys=True))
