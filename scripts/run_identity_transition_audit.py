from __future__ import annotations

import json

from abx.identity.transitionReports import build_identity_transition_report


if __name__ == "__main__":
    print(json.dumps(build_identity_transition_report(), indent=2, sort_keys=True))
