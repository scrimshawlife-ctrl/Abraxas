from __future__ import annotations

import json

from abx.reconcile.reconciliationReports import build_reconciliation_report


if __name__ == "__main__":
    print(json.dumps(build_reconciliation_report(), indent=2, sort_keys=True))
