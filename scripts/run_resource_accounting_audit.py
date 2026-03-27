from __future__ import annotations

import json

from abx.performance.accountingReports import build_resource_accounting_report


if __name__ == "__main__":
    print(json.dumps(build_resource_accounting_report(), indent=2, sort_keys=True))
