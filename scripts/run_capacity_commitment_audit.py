from __future__ import annotations

import json

from abx.capacity.commitmentReports import build_capacity_commitment_report


if __name__ == "__main__":
    print(json.dumps(build_capacity_commitment_report(), indent=2, sort_keys=True))
