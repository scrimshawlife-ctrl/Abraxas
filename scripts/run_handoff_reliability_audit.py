from __future__ import annotations

import json

from abx.interface.handoffReports import build_handoff_reliability_report


if __name__ == "__main__":
    print(json.dumps(build_handoff_reliability_report(), indent=2, sort_keys=True))
