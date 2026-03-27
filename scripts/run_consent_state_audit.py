from __future__ import annotations

import json

from abx.approval.consentReports import build_consent_state_report


if __name__ == "__main__":
    print(json.dumps(build_consent_state_report(), indent=2, sort_keys=True))
