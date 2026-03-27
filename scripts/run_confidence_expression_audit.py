from __future__ import annotations

import json

from abx.uncertainty.confidenceExpressionReports import build_confidence_expression_report


if __name__ == "__main__":
    print(json.dumps(build_confidence_expression_report(), indent=2, sort_keys=True))
