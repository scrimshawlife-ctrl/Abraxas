#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.federation.capabilityReports import build_capability_registry_report


def main() -> None:
    print(json.dumps(build_capability_registry_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
