from __future__ import annotations

import json

from abx.human_factors.interactionReports import build_interaction_audit_report


if __name__ == "__main__":
    print(json.dumps(build_interaction_audit_report(), indent=2, sort_keys=True))
