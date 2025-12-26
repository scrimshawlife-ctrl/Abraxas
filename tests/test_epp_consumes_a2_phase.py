from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.epp_builder import build_epp


def test_epp_consumes_a2_phase(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    a2_phase_payload = {
        "version": "a2_phase.v0.1",
        "run_id": "run123",
        "ts": "2025-01-01T00:00:00Z",
        "registry": "out/a2_registry/terms.jsonl",
        "profiles": [
            {
                "term_key": "k1",
                "term": "alpha",
                "v14": 1.2,
                "v60": 0.4,
                "phase": "surging",
                "manipulation_risk_mean": 0.3,
            },
            {
                "term_key": "k2",
                "term": "beta",
                "v14": 0.9,
                "v60": 0.6,
                "phase": "resurgent",
                "manipulation_risk_mean": 0.4,
            },
        ],
        "provenance": {"builder": "abx.a2_phase.v0.1"},
    }
    a2_phase_path = reports_dir / "a2_phase_run123.json"
    a2_phase_path.write_text(json.dumps(a2_phase_payload), encoding="utf-8")

    ledger_path = tmp_path / "value_ledgers" / "epp_runs.jsonl"
    json_path, _ = build_epp(
        run_id="run123",
        out_dir=str(reports_dir),
        inputs_dir=str(reports_dir),
        osh_ledger_path=str(tmp_path / "osh.jsonl"),
        a2_phase_path=str(a2_phase_path),
        ledger_path=str(ledger_path),
        ts="2025-01-01T00:00:00Z",
    )

    report = json.loads(Path(json_path).read_text(encoding="utf-8"))
    proposals = report.get("proposals", [])
    watch_terms = [
        proposal.get("recommended_change", {}).get("watch_terms", [])
        for proposal in proposals
        if proposal.get("kind") == "COMPONENT_FOCUS_SUGGESTION"
    ]
    assert any("alpha" in terms for terms in watch_terms)
