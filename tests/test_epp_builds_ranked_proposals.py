from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.epp_builder import build_epp


def test_epp_builds_ranked_proposals(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    smv_src = Path("tests/fixtures/epp/sample_smv.json").read_text()
    cre_src = Path("tests/fixtures/epp/sample_cre.json").read_text()
    dap_src = Path("tests/fixtures/epp/sample_dap.json").read_text()
    osh_src = Path("tests/fixtures/epp/sample_osh_ledger.jsonl").read_text()

    (reports_dir / "smv_run123_portfolio_a.json").write_text(smv_src)
    (reports_dir / "cre_run123_portfolio_a.json").write_text(cre_src)
    (reports_dir / "dap_run123.json").write_text(dap_src)

    osh_dir = tmp_path / "osh_ledgers"
    osh_dir.mkdir()
    osh_ledger = osh_dir / "fetch_artifacts.jsonl"
    osh_ledger.write_text(osh_src)

    ledger_path = tmp_path / "value_ledgers" / "epp_runs.jsonl"

    json_path, md_path = build_epp(
        run_id="run123",
        out_dir=str(reports_dir),
        inputs_dir=str(reports_dir),
        osh_ledger_path=str(osh_ledger),
        ledger_path=str(ledger_path),
        ts="2025-01-01T00:00:00Z",
    )

    report = json.loads(Path(json_path).read_text())
    kinds = {proposal["kind"] for proposal in report["proposals"]}
    assert "SIW_TIGHTEN_SOURCE" in kinds
    assert "SIW_LOOSEN_SOURCE" in kinds
    assert "VECTOR_NODE_CADENCE_CHANGE" in kinds
    assert "OFFLINE_EVIDENCE_ESCALATION" in kinds
    assert "COMPONENT_FOCUS_SUGGESTION" in kinds

    md_text = Path(md_path).read_text()
    assert "Top tighten candidates" in md_text
    assert "Top loosen candidates" in md_text
    assert "Cadence changes" in md_text
    assert "Offline escalations" in md_text
