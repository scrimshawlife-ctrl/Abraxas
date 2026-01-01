from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.canon_diff import build_canon_diff


def test_canon_diff_handles_missing_canon(tmp_path: Path):
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps({"overlay": {"intents": {"p1": {"kind": "X", "target": {}}}}}),
        encoding="utf-8",
    )
    out_reports = tmp_path / "reports"
    json_path, md_path, _ = build_canon_diff(
        run_id="r1",
        out_reports_dir=str(out_reports),
        candidate_policy_path=str(candidate),
        canon_snapshot_path=None,
    )
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    assert "no_canon_snapshot_found" in data["notes"]
    assert Path(md_path).exists()
