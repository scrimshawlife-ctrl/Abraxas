from __future__ import annotations

import json

from abx.meta.canonResolutionReports import build_canon_conflict_audit_report


if __name__ == "__main__":
    print(json.dumps(build_canon_conflict_audit_report(), indent=2, sort_keys=True))
