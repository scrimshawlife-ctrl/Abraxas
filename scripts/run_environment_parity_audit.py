#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.deployment.environmentReports import build_environment_parity_report


if __name__ == "__main__":
    print(json.dumps(build_environment_parity_report(), indent=2, sort_keys=True))
