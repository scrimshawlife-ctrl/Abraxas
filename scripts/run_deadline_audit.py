from __future__ import annotations

import json

from abx.obligations.dueStateReports import build_due_state_report


if __name__ == "__main__":
    print(json.dumps(build_due_state_report(), indent=2, sort_keys=True))
