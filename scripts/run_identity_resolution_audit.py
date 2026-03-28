from __future__ import annotations

import json

from abx.identity.identityReports import build_identity_resolution_report


if __name__ == "__main__":
    print(json.dumps(build_identity_resolution_report(), indent=2, sort_keys=True))
