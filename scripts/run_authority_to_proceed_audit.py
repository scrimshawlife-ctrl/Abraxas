from __future__ import annotations

import json

from abx.approval.authorityReports import build_authority_report


if __name__ == "__main__":
    print(json.dumps(build_authority_report(), indent=2, sort_keys=True))
