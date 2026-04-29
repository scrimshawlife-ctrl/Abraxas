from __future__ import annotations
import json
import sys
from abx.repair.scenario_engine import run_scenario_batch


def main(argv: list[str]) -> int:
    write_artifacts = "--write-artifacts" in argv[1:]
    scenario_set = "starter"
    if "--scenario-set" in argv[1:]:
        idx = argv.index("--scenario-set")
        if idx + 1 < len(argv):
            scenario_set = argv[idx + 1]
    out = run_scenario_batch(write_artifacts=write_artifacts, scenario_set=scenario_set)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
