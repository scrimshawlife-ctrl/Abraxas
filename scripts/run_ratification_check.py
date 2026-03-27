from __future__ import annotations

import json

from abx.closure.ratificationReports import build_ratification_report


if __name__ == "__main__":
    print(json.dumps(build_ratification_report(), indent=2, sort_keys=True))
