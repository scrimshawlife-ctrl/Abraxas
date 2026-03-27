from __future__ import annotations

import json

from abx.lineage.mutationReports import build_mutation_report


if __name__ == "__main__":
    print(json.dumps(build_mutation_report(), indent=2, sort_keys=True))
