"""
Tests for component score ledger hash chaining.
"""

from abraxas.scoreboard.component_ledger import ComponentScoreLedger


def test_component_scores_ledger_chain(tmp_path):
    ledger_path = tmp_path / "component_scores.jsonl"
    ledger = ComponentScoreLedger(ledger_path=ledger_path)

    summary_a = {
        "n": 3,
        "hit_rate": 0.5,
        "brier_avg": 0.2,
        "coverage_rate": None,
        "trend_acc": None,
        "abstain_rate": 0.0,
        "unknown_rate": 0.33,
    }
    summary_b = {
        "n": 2,
        "hit_rate": 1.0,
        "brier_avg": 0.1,
        "coverage_rate": None,
        "trend_acc": None,
        "abstain_rate": 0.0,
        "unknown_rate": 0.0,
    }

    first_hash = ledger.append_score("run_001", "COMP_A", "H72H", summary_a)
    second_hash = ledger.append_score("run_001", "COMP_B", "H72H", summary_b)

    assert ledger_path.exists()
    lines = ledger_path.read_text().strip().splitlines()
    assert len(lines) == 2
    assert first_hash in lines[0]
    assert second_hash in lines[1]
