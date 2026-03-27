from __future__ import annotations

import json

from abx.docs_governance.roleReports import build_role_legibility_audit_report


if __name__ == "__main__":
    print(json.dumps(build_role_legibility_audit_report(), indent=2, sort_keys=True))
