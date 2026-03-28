from __future__ import annotations

import json

from abx.reconcile.restorationReports import build_restoration_status_report


if __name__ == "__main__":
    print(json.dumps(build_restoration_status_report(), indent=2, sort_keys=True))
