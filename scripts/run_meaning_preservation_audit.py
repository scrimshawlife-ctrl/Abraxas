from __future__ import annotations

import json

from abx.semantic.meaningReports import build_meaning_preservation_report


if __name__ == "__main__":
    print(json.dumps(build_meaning_preservation_report(), indent=2, sort_keys=True))
