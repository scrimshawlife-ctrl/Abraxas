from __future__ import annotations

import json

from abx.semantic.compatibilityReports import build_schema_evolution_report


if __name__ == "__main__":
    print(json.dumps(build_schema_evolution_report(), indent=2, sort_keys=True))
