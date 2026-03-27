from __future__ import annotations

import json

from abx.epistemics.qualityReports import build_epistemic_quality_audit_report


if __name__ == "__main__":
    print(json.dumps(build_epistemic_quality_audit_report(), indent=2, sort_keys=True))
