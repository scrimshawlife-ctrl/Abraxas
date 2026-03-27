from __future__ import annotations

import json

from abx.lineage.provenanceReports import build_provenance_report


if __name__ == "__main__":
    print(json.dumps(build_provenance_report(), indent=2, sort_keys=True))
