from __future__ import annotations

import json

from abx.explanation.boundaryReports import build_explanation_boundary_report


if __name__ == "__main__":
    print(json.dumps(build_explanation_boundary_report(), indent=2, sort_keys=True))
