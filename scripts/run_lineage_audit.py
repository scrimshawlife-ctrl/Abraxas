from __future__ import annotations

import json

from abx.lineage.lineageReports import build_lineage_report


if __name__ == "__main__":
    print(json.dumps(build_lineage_report(), indent=2, sort_keys=True))
