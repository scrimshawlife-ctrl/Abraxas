from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from abraxas_ase.candidates import load_candidates_jsonl
from abraxas_ase.provenance import stable_json_dumps
from abraxas_ase.stabilization import StabilizationParams, can_seal_core


def _write_list(path: Path, words: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(set(words))) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(prog="python -m abraxas_ase.tools.promote_lanes")
    ap.add_argument("--candidates", required=True, help="Path to candidates.jsonl snapshot")
    ap.add_argument("--lanes-dir", required=True, help="lexicon_sources/lanes")
    ap.add_argument("--core-file", required=True, help="lexicon_sources/subwords_core.txt")
    ap.add_argument("--apply", action="store_true", help="Write lane files + core file. Without --apply, dry run.")
    args = ap.parse_args()

    cand = load_candidates_jsonl(args.candidates)
    stab_params = StabilizationParams()

    shadow = []
    canary = []
    core = []
    core_blocked = 0

    for (kind, name), r in cand.items():
        if kind != "subword":
            continue
        if r.lane == "shadow":
            shadow.append(name)
        elif r.lane == "canary":
            canary.append(name)
        elif r.lane == "core":
            if can_seal_core(r.cycles_alive, r.cycles_stable, stab_params):
                core.append(name)
            else:
                core_blocked += 1

    lanes_dir = Path(args.lanes_dir)
    shadow_path = lanes_dir / "shadow.txt"
    canary_path = lanes_dir / "canary.txt"
    core_path = lanes_dir / "core.txt"

    # core file merges: existing subwords_core.txt + promoted core lane
    core_file = Path(args.core_file)
    existing_core = []
    if core_file.exists():
        existing_core = [ln.strip().lower() for ln in core_file.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]

    merged_core = sorted(set(existing_core + core))

    report = {
        "shadow_count": len(set(shadow)),
        "canary_count": len(set(canary)),
        "core_lane_count": len(set(core)),
        "core_lane_blocked": core_blocked,
        "core_file_count": len(merged_core),
        "writes": {
            "shadow": str(shadow_path),
            "canary": str(canary_path),
            "core_lane": str(core_path),
            "core_file": str(core_file),
        },
    }

    if not args.apply:
        print(stable_json_dumps({"status":"dry_run", **report}))
        return

    _write_list(shadow_path, shadow)
    _write_list(canary_path, canary)
    _write_list(core_path, core)
    _write_list(core_file, merged_core)

    print(stable_json_dumps({"status":"ok", **report}))


if __name__ == "__main__":
    main()
