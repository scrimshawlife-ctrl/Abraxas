from __future__ import annotations

import json
import subprocess
from pathlib import Path

from abraxas_ase.candidates import CandidateRec, write_candidates_jsonl


def test_promote_lanes_dry_run(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.jsonl"
    lanes_dir = tmp_path / "lanes"
    core_file = tmp_path / "subwords_core.txt"
    lanes_dir.mkdir(parents=True)
    (lanes_dir / "shadow.txt").write_text("shadowword\n", encoding="utf-8")
    (lanes_dir / "canary.txt").write_text("canaryword\n", encoding="utf-8")
    (lanes_dir / "core.txt").write_text("coreword\n", encoding="utf-8")
    core_file.write_text("corebase\n", encoding="utf-8")

    recs = [
        CandidateRec("alpha", "subword", "2026-01-01", "2026-01-01", 1, ["ap"], ["e"], 0.0, 1.0, 0.0, 1, "shadow"),
        CandidateRec("beta", "subword", "2026-01-01", "2026-01-01", 1, ["ap"], ["e"], 0.0, 1.0, 0.0, 1, "canary"),
        CandidateRec("gamma", "subword", "2026-01-01", "2026-01-01", 1, ["ap"], ["e"], 0.0, 1.0, 0.0, 1, "core"),
    ]
    write_candidates_jsonl(str(candidates_path), recs)

    cmd = [
        "python",
        "-m",
        "abraxas_ase.tools.promote_lanes",
        "--candidates",
        str(candidates_path),
        "--lanes-dir",
        str(lanes_dir),
        "--core-file",
        str(core_file),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "dry_run"

    assert (lanes_dir / "shadow.txt").read_text(encoding="utf-8") == "shadowword\n"
    assert (lanes_dir / "canary.txt").read_text(encoding="utf-8") == "canaryword\n"
    assert (lanes_dir / "core.txt").read_text(encoding="utf-8") == "coreword\n"
    assert core_file.read_text(encoding="utf-8") == "corebase\n"
