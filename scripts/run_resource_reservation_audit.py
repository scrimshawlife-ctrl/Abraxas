from __future__ import annotations

import json

from abx.capacity.reservationReports import build_resource_reservation_report


if __name__ == "__main__":
    print(json.dumps(build_resource_reservation_report(), indent=2, sort_keys=True))
