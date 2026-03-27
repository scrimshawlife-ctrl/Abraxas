from __future__ import annotations

import json

from abx.failure.errorReports import build_error_taxonomy_report


if __name__ == "__main__":
    print(json.dumps(build_error_taxonomy_report(), indent=2, sort_keys=True))
