from __future__ import annotations

import json

from abx.docs_governance.handoffReports import build_handoff_audit_report


if __name__ == "__main__":
    print(json.dumps(build_handoff_audit_report(), indent=2, sort_keys=True))
