from __future__ import annotations

import json

from abx.agency.delegationReports import build_delegation_report


if __name__ == "__main__":
    print(json.dumps(build_delegation_report(), indent=2, sort_keys=True))
