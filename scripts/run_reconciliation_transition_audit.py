from __future__ import annotations

import json

from abx.reconcile.transitionReports import build_reconciliation_transition_report


if __name__ == "__main__":
    print(json.dumps(build_reconciliation_transition_report(), indent=2, sort_keys=True))
