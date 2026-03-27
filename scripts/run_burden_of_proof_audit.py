from __future__ import annotations

import json

from abx.evidence.sufficiencyReports import build_sufficiency_report


if __name__ == "__main__":
    print(json.dumps(build_sufficiency_report(), indent=2, sort_keys=True))
