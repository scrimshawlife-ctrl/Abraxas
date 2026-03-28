from __future__ import annotations

import json

from abx.identity.persistenceReports import build_entity_persistence_report


if __name__ == "__main__":
    print(json.dumps(build_entity_persistence_report(), indent=2, sort_keys=True))
