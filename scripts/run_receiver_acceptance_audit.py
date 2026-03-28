from __future__ import annotations

import json

from abx.interface.acceptanceReports import build_receiver_acceptance_report


if __name__ == "__main__":
    print(json.dumps(build_receiver_acceptance_report(), indent=2, sort_keys=True))
