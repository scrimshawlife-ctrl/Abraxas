from __future__ import annotations

import json

from abx.explanation.compressionReports import build_narrative_compression_report


if __name__ == "__main__":
    print(json.dumps(build_narrative_compression_report(), indent=2, sort_keys=True))
