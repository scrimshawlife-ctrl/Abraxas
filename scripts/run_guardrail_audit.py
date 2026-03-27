from __future__ import annotations

import json

from abx.agency.guardrailReports import build_guardrail_report


if __name__ == "__main__":
    print(json.dumps(build_guardrail_report(), indent=2, sort_keys=True))
