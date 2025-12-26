from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.evogate_builder import build_evogate


def test_evogate_writes_candidate_policy_and_report(tmp_path: Path):
    epp_path = tmp_path / "epp.json"
    epp_path.write_text(
        json.dumps(
            {
                "pack_id": "p1",
                "proposals": [
                    {
                        "proposal_id": "x1",
                        "kind": "OFFLINE_EVIDENCE_ESCALATION",
                        "target": {"unit_id": "dap"},
                        "recommended_change": {
                            "user_prompt": "evidence_pack_required"
                        },
                        "expected_impact": {
                            "metric": "coverage_rate",
                            "delta": 0.01
                        },
                        "risk": {"integrity_risk": 0.1},
                        "confidence": 0.7,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    baseline_path = Path("tests/fixtures/evogate/sample_baseline_metrics.json")
    out_reports = tmp_path / "reports"
    staging_root = tmp_path / "staging"

    replay_cmd = "python -m tests.helpers.fake_replay_cmd"
    json_path, _, meta = build_evogate(
        run_id="r1",
        out_reports_dir=str(out_reports),
        staging_root_dir=str(staging_root),
        epp_path=str(epp_path),
        baseline_metrics_path=str(baseline_path),
        replay_cmd=replay_cmd,
    )
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    assert data["run_id"] == "r1"
    assert "candidate_policy_path" in data
    candidate_path = Path(data["candidate_policy_path"])
    assert candidate_path.exists()
    candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
    assert candidate.get("version") == "candidate_policy.v0.1"
    assert meta["applied"] == 1
    assert data["replay"]["provenance"]["method"] == "command"
