from __future__ import annotations

import json

from abx.failure.recoveryReports import build_recovery_eligibility_report


if __name__ == "__main__":
    print(json.dumps(build_recovery_eligibility_report(), indent=2, sort_keys=True))
