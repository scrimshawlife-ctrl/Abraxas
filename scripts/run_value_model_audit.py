#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.governance.valueReports import build_value_audit_report


def main() -> None:
    print(json.dumps(build_value_audit_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
