from __future__ import annotations

import json

from abx.obligations.obligationReports import build_obligation_lifecycle_report


if __name__ == "__main__":
    print(json.dumps(build_obligation_lifecycle_report(), indent=2, sort_keys=True))
