from __future__ import annotations

import json

from abx.outcome.effectRealizationReports import build_effect_realization_report


if __name__ == "__main__":
    print(json.dumps(build_effect_realization_report(), indent=2, sort_keys=True))
