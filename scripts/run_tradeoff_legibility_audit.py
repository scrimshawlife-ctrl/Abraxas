from __future__ import annotations

import json

from abx.tradeoff.tradeoffReports import build_tradeoff_legibility_report


if __name__ == "__main__":
    print(json.dumps(build_tradeoff_legibility_report(), indent=2, sort_keys=True))
