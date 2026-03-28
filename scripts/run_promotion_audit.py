from __future__ import annotations

import json

from abx.admission.promotionReports import build_promotion_gate_report


if __name__ == "__main__":
    print(json.dumps(build_promotion_gate_report(), indent=2, sort_keys=True))
