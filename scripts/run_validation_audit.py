from __future__ import annotations

import json

from abx.epistemics.validationReports import build_validation_audit_report


if __name__ == "__main__":
    print(json.dumps(build_validation_audit_report(), indent=2, sort_keys=True))
