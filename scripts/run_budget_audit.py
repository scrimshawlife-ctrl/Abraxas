from __future__ import annotations

import json

from abx.performance.budgetReports import build_budget_audit_report


if __name__ == "__main__":
    print(json.dumps(build_budget_audit_report(), indent=2, sort_keys=True))
