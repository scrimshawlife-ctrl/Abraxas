from __future__ import annotations

import json

from abx.outcome.postActionTruthReports import build_post_action_truth_report


if __name__ == "__main__":
    print(json.dumps(build_post_action_truth_report(), indent=2, sort_keys=True))
