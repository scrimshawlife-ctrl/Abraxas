from __future__ import annotations

import json

from abx.identity.coherenceReports import build_referential_coherence_report


if __name__ == "__main__":
    print(json.dumps(build_referential_coherence_report(), indent=2, sort_keys=True))
