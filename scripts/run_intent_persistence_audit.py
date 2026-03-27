from __future__ import annotations

import json

from abx.continuity.persistenceReports import build_intent_persistence_report


if __name__ == "__main__":
    print(json.dumps(build_intent_persistence_report(), indent=2, sort_keys=True))
