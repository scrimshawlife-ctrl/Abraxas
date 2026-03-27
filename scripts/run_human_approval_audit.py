from __future__ import annotations

import json

from abx.approval.approvalReports import build_human_approval_report


if __name__ == "__main__":
    print(json.dumps(build_human_approval_report(), indent=2, sort_keys=True))
