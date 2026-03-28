from __future__ import annotations

import json

from abx.semantic.semanticReports import build_semantic_drift_report


if __name__ == "__main__":
    print(json.dumps(build_semantic_drift_report(), indent=2, sort_keys=True))
