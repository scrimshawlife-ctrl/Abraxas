from __future__ import annotations

import json

from abx.obligations.commitmentReports import build_external_commitment_report


if __name__ == "__main__":
    print(json.dumps(build_external_commitment_report(), indent=2, sort_keys=True))
