from __future__ import annotations

import json

from abx.innovation.researchReports import build_research_artifact_audit_report


if __name__ == "__main__":
    print(json.dumps(build_research_artifact_audit_report(), indent=2, sort_keys=True))
