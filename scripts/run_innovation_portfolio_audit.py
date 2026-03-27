from __future__ import annotations

import json

from abx.innovation.portfolioReports import build_innovation_portfolio_audit_report


if __name__ == "__main__":
    print(json.dumps(build_innovation_portfolio_audit_report(), indent=2, sort_keys=True))
