from __future__ import annotations

import json

from abx.admission.releaseReports import build_release_readiness_report


if __name__ == "__main__":
    print(json.dumps(build_release_readiness_report(), indent=2, sort_keys=True))
