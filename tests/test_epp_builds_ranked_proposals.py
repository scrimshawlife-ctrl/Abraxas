from __future__ import annotations

import json
from pathlib import Path

from abraxas.evolve.epp_builder import build_epp

FIXTURES = Path("tests/fixtures/epp")

ALL_KINDS = {
    "SIW_TIGHTEN_SOURCE",
    "SIW_LOOSEN_SOURCE",
    "VECTOR_NODE_CADENCE_CHANGE",
    "OFFLINE_EVIDENCE_ESCALATION",
    "COMPONENT_FOCUS_SUGGESTION",
}


def _run_epp(tmp_path, osh_ledger_name: str):
    """Run the EPP builder against one OSH ledger fixture.

    The builder derives a SINGLE global composite risk per run from the OSH
    transport failure rate. Because SIW_TIGHTEN requires risk >= 0.6 and
    SIW_LOOSEN requires risk <= 0.3, the two are mutually exclusive within any
    one run — they cannot both appear from a single fixture. Each fixture is
    therefore exercised in its own run.
    """
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    (reports_dir / "smv_run123_portfolio_a.json").write_text(
        (FIXTURES / "sample_smv.json").read_text()
    )
    (reports_dir / "cre_run123_portfolio_a.json").write_text(
        (FIXTURES / "sample_cre.json").read_text()
    )
    (reports_dir / "dap_run123.json").write_text(
        (FIXTURES / "sample_dap.json").read_text()
    )

    osh_dir = tmp_path / "osh_ledgers"
    osh_dir.mkdir(parents=True, exist_ok=True)
    osh_ledger = osh_dir / "fetch_artifacts.jsonl"
    osh_ledger.write_text((FIXTURES / osh_ledger_name).read_text())

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
    return kinds, Path(md_path).read_text(), report


def test_epp_builds_ranked_proposals(tmp_path):
    """HIGH transport-failure profile -> tighten / escalate lane."""
    kinds, md_text, report = _run_epp(tmp_path, "sample_osh_ledger.jsonl")

    # Ranked: every proposal carries a rationale score, and the report orders
    # proposals by descending score.
    assert report["proposals"], "expected at least one proposal"
    for proposal in report["proposals"]:
        assert "kind" in proposal
        assert "rationale" in proposal
        assert "score" in proposal["rationale"]

    scores = [p["rationale"]["score"] for p in report["proposals"]]
    assert scores == sorted(scores, reverse=True), "proposals must be ranked by score"

    # HIGH risk lane: tighten + escalate, never loosen.
    assert "SIW_TIGHTEN_SOURCE" in kinds
    assert "OFFLINE_EVIDENCE_ESCALATION" in kinds
    assert "VECTOR_NODE_CADENCE_CHANGE" in kinds
    assert "COMPONENT_FOCUS_SUGGESTION" in kinds
    assert "SIW_LOOSEN_SOURCE" not in kinds, (
        "SIW_LOOSEN_SOURCE requires composite risk <= 0.3; this fixture's "
        "transport failure rate places risk well above that"
    )

    assert "Top tighten candidates" in md_text
    assert "Cadence changes" in md_text
    assert "Offline escalations" in md_text


def test_epp_builds_ranked_proposals_low_risk(tmp_path):
    """LOW transport-failure profile -> loosen lane.

    Completes the coverage contract: together with the HIGH-risk run above,
    every proposal kind the builder can emit is reachable.
    """
    kinds, md_text, _ = _run_epp(tmp_path, "sample_osh_ledger_low_risk.jsonl")

    assert "SIW_LOOSEN_SOURCE" in kinds
    assert "VECTOR_NODE_CADENCE_CHANGE" in kinds
    assert "COMPONENT_FOCUS_SUGGESTION" in kinds
    assert "SIW_TIGHTEN_SOURCE" not in kinds, (
        "SIW_TIGHTEN_SOURCE requires composite risk >= 0.6; this fixture's "
        "transport failure rate places risk well below that"
    )

    assert "Top loosen candidates" in md_text


def test_epp_reaches_every_proposal_kind(tmp_path):
    """Every proposal kind is reachable across the two risk profiles."""
    high_kinds, _, _ = _run_epp(tmp_path / "high", "sample_osh_ledger.jsonl")
    low_kinds, _, _ = _run_epp(tmp_path / "low", "sample_osh_ledger_low_risk.jsonl")

    assert high_kinds | low_kinds == ALL_KINDS, (
        f"unreachable kinds: {sorted(ALL_KINDS - (high_kinds | low_kinds))}"
    )
