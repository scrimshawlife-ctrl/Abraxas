from __future__ import annotations

import json

from abx.closure.closureReports import build_system_closure_report


if __name__ == "__main__":
    print(json.dumps(build_system_closure_report(), indent=2, sort_keys=True))
