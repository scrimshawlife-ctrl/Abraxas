from __future__ import annotations

import json

from abx.semantic.transitionReports import build_semantic_transition_report


if __name__ == "__main__":
    print(json.dumps(build_semantic_transition_report(), indent=2, sort_keys=True))
