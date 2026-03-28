from __future__ import annotations

import json

from abx.operator.overrideReports import build_override_report


if __name__ == "__main__":
    print(json.dumps(build_override_report(), indent=2, sort_keys=True))
