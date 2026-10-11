from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.truth_contamination as truth_contamination


def _write_json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row) for row in rows)
    path.write_text(text + ("\n" if text else ""), encoding="utf-8")
    return str(path)


def _prepare_default_cli_tree(root: Path) -> None:
    reports = root / "out" / "reports"
    _write_json(reports / "evidence_metrics_a.json", {"claim_scores": {"stale": {}}})
    _write_json(reports / "evidence_metrics_z.json", {"claim_scores": {}})
    _write_json(reports / "proof_integrity_a.json", {"PIS": 1})
    _write_json(reports / "sig_kpi_a.json", {"PDG": {"avg_unique_domains_per_term": 6}})
    _write_json(reports / "regime_shift_a.json", {"regime_shift": True})
    _write_jsonl(root / "out" / "ledger" / "evidence_graph.jsonl", [])
    _write_jsonl(root / "out" / "ledger" / "anchor_ledger.jsonl", [])


def test_fingerprint_normalizes_repeated_claim_text() -> None:
    first = truth_contamination._fingerprint(
        "A repeated claim has a stable phrase: https://example.test/item?ref=123!"
    )
    second = truth_contamination._fingerprint("a repeated claim has a stable phrase")

    assert first
    assert first == second


def test_compute_truth_map_classifies_a_coherent_claim(tmp_path: Path) -> None:
    evidence_metrics = _write_json(
        tmp_path / "evidence.json",
        {
            "claim_scores": {
                "claim-1": {
                    "CSS": 1,
                    "CPR": 0,
                    "support_domains": 6,
                    "contra_domains": 0,
                }
            }
        },
    )
    proof_integrity = _write_json(tmp_path / "proof.json", {"PIS": 1})
    sig_kpi = _write_json(
        tmp_path / "sig.json",
        {
            "PDG": {
                "avg_unique_domains_per_term": 6,
                "avg_falsification_tests_per_term": 3,
            }
        },
    )

    result = truth_contamination.compute_truth_map(
        evidence_metrics_path=evidence_metrics,
        proof_integrity_path=proof_integrity,
        sig_kpi_path=sig_kpi,
        tpl_coord={
            "tpl_by_claim": {"claim-1": {"TPL": 0}},
            "coord_by_claim": {"claim-1": {"COORD": 0}},
        },
    )

    assert result["claims"]["claim-1"]["quadrant"] == "LEGIT_PATTERN"
    assert result["quadrant_counts"] == {"LEGIT_PATTERN": 1}
    assert result["globals"]["regime_shift"] is False


def test_read_json_returns_empty_for_missing_invalid_and_non_object_inputs(
    tmp_path: Path,
) -> None:
    assert truth_contamination._read_json(str(tmp_path / "missing.json")) == {}

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not-json", encoding="utf-8")
    assert truth_contamination._read_json(str(invalid)) == {}

    array = Path(_write_json(tmp_path / "array.json", []))
    assert truth_contamination._read_json(str(array)) == {}


def test_read_jsonl_skips_blank_malformed_and_non_object_rows(tmp_path: Path) -> None:
    assert truth_contamination._read_jsonl("") == []
    assert truth_contamination._read_jsonl(str(tmp_path / "missing.jsonl")) == []

    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text('\n{"first": 1}\n[]\nnot-json\n {"second": 2} \n', encoding="utf-8")

    assert truth_contamination._read_jsonl(str(ledger)) == [
        {"first": 1},
        {"second": 2},
    ]


def test_latest_returns_last_sorted_match_or_empty_string(tmp_path: Path) -> None:
    (tmp_path / "report_a.json").touch()
    (tmp_path / "report_z.json").touch()

    assert truth_contamination._latest(str(tmp_path), "report_*.json") == str(
        tmp_path / "report_z.json"
    )
    assert truth_contamination._latest(str(tmp_path), "absent_*.json") == ""


def test_clamp_bounds_values_and_preserves_values_inside_range() -> None:
    assert truth_contamination._clamp(-0.2) == 0.0
    assert truth_contamination._clamp(1.2) == 1.0
    assert truth_contamination._clamp(0.4) == 0.4
    assert truth_contamination._clamp(0.5, 0.2, 0.8) == 0.5


def test_sigmoid_handles_positive_and_negative_inputs() -> None:
    assert truth_contamination._sigmoid(0) == pytest.approx(0.5)
    assert truth_contamination._sigmoid(8) > 0.99
    assert truth_contamination._sigmoid(-8) < 0.01


def test_fingerprint_ignores_short_text() -> None:
    assert truth_contamination._fingerprint("too short") == ""


@pytest.mark.parametrize(
    ("ml_score", "cs_score", "expected"),
    [
        (0.59, 0.60, "LEGIT_PATTERN"),
        (0.60, 0.60, "WEAPONIZED_TRUTH"),
        (0.60, 0.59, "LIKELY_MANIPULATION"),
        (0.59, 0.59, "BENIGN_NOISE"),
    ],
)
def test_quadrant_classifies_all_score_combinations(
    ml_score: float, cs_score: float, expected: str
) -> None:
    assert truth_contamination._quadrant(ml_score, cs_score) == expected


def test_build_tpl_coord_from_ledgers_uses_recent_runs_and_domain_reuse(
    tmp_path: Path,
) -> None:
    anchors = [
        {"run_id": "old-run", "kind": "anchor_added"},
        {"run_id": "run-2", "kind": "anchor_added"},
        {"run_id": "run-3", "kind": "other"},
        {"run_id": "run-3", "kind": "anchor_added"},
        {"run_id": "run-3", "kind": "anchor_added"},
        {"run_id": "", "kind": "anchor_added"},
    ]
    repeated_text = "A common claim template repeats across multiple domains."
    unique_text = "A distinct one-off claim has enough words for a fingerprint."
    evidence = [
        {"kind": "other", "run_id": "run-3", "claim_id": "ignored", "text": repeated_text},
        *[
            {
                "kind": "claim_added",
                "run_id": "run-2" if index % 2 else "run-3",
                "claim_id": f"claim-{index}",
                "text": repeated_text,
            }
            for index in range(1, 6)
        ],
        {
            "kind": "claim_added",
            "run_id": "run-3",
            "claim_id": "claim-6",
            "text": unique_text,
        },
        {"kind": "claim_added", "run_id": "run-3", "claim_id": "short", "text": "short"},
        {"kind": "claim_added", "run_id": "old-run", "claim_id": "old", "text": repeated_text},
        {"kind": "claim_added", "run_id": "run-3", "claim_id": "", "text": repeated_text},
        *[
            {
                "kind": "anchor_claim_link",
                "run_id": "run-3" if index % 2 else "run-2",
                "claim_id": f"claim-{index}",
                "domain": domain,
            }
            for index, domain in enumerate(("d1", "d2", "d3", "d4", "d4"), start=1)
        ],
        {"kind": "anchor_claim_link", "run_id": "old-run", "claim_id": "claim-1", "domain": "old"},
        {"kind": "anchor_claim_link", "run_id": "run-3", "claim_id": "claim-6"},
        {"kind": "anchor_claim_link", "run_id": "run-3", "claim_id": "ghost", "domain": "ghost"},
    ]
    evidence_path = _write_jsonl(tmp_path / "evidence.jsonl", evidence)
    anchor_path = _write_jsonl(tmp_path / "anchors.jsonl", anchors)

    result = truth_contamination.build_tpl_coord_from_ledgers(
        evidence_graph_ledger=evidence_path,
        anchor_ledger=anchor_path,
        window_runs=2,
    )

    assert result["version"] == "tpl_coord.v0.1"
    assert result["window_runs"] == 2
    assert result["n_claim_texts"] == 7
    assert set(result["tpl_by_claim"]) == {*(f"claim-{i}" for i in range(1, 7))}
    for index in range(1, 6):
        assert result["tpl_by_claim"][f"claim-{index}"]["TPL"] == 1.0
        assert result["tpl_by_claim"][f"claim-{index}"]["repetitions"] == 5
        assert result["coord_by_claim"][f"claim-{index}"]["COORD"] == 1.0
        assert result["coord_by_claim"][f"claim-{index}"]["template_domains"] == 4
    assert result["tpl_by_claim"]["claim-6"]["TPL"] == 0.0
    assert result["coord_by_claim"]["claim-6"]["COORD"] == 0.0
    assert "short" not in result["tpl_by_claim"]
    assert "old" not in result["tpl_by_claim"]


def test_build_tpl_coord_from_missing_ledgers_returns_empty_maps(tmp_path: Path) -> None:
    result = truth_contamination.build_tpl_coord_from_ledgers(
        evidence_graph_ledger=str(tmp_path / "missing-evidence.jsonl"),
        anchor_ledger=str(tmp_path / "missing-anchors.jsonl"),
    )

    assert result["n_claim_texts"] == 0
    assert result["tpl_by_claim"] == {}
    assert result["coord_by_claim"] == {}


def test_compute_truth_map_scores_and_counts_all_quadrants(tmp_path: Path) -> None:
    evidence_metrics = _write_json(
        tmp_path / "evidence.json",
        {
            "claim_scores": {
                "legit": {"CSS": 1, "CPR": 0, "support_domains": 6},
                "weaponized": {"CSS": 1, "CPR": 0, "support_domains": 6},
                "manipulation": {"CSS": 0, "CPR": 0},
                "noise": {"CSS": 0, "CPR": 0},
                "defaults": {},
                "ignored": "not-a-claim-object",
            }
        },
    )
    proof_integrity = _write_json(tmp_path / "proof.json", {"PIS": 1})
    sig_kpi = _write_json(
        tmp_path / "sig.json",
        {
            "PDG": {
                "avg_unique_domains_per_term": 6,
                "avg_falsification_tests_per_term": 3,
            }
        },
    )
    result = truth_contamination.compute_truth_map(
        evidence_metrics_path=evidence_metrics,
        proof_integrity_path=proof_integrity,
        sig_kpi_path=sig_kpi,
        tpl_coord={
            "tpl_by_claim": {
                "legit": {"TPL": 0},
                "weaponized": {"TPL": 1},
                "manipulation": {"TPL": 1},
                "noise": {"TPL": 0},
            },
            "coord_by_claim": {
                "legit": {"COORD": 0},
                "weaponized": {"COORD": 1},
                "manipulation": {"COORD": 1},
                "noise": {"COORD": 0},
            },
        },
    )

    assert result["version"] == "truth_contamination.v0.1"
    assert result["quadrant_counts"] == {
        "LEGIT_PATTERN": 1,
        "WEAPONIZED_TRUTH": 1,
        "LIKELY_MANIPULATION": 1,
        "BENIGN_NOISE": 2,
    }
    assert set(result["claims"]) == {"legit", "weaponized", "manipulation", "noise", "defaults"}
    assert result["claims"]["legit"]["CS_score"] == pytest.approx(1.0)
    assert result["claims"]["weaponized"]["ML_score"] == pytest.approx(0.7)
    assert result["claims"]["defaults"]["inputs"]["TPL"] == 0.0
    assert result["claims"]["defaults"]["inputs"]["COORD"] == 0.0
    assert result["claims"]["legit"]["inputs"]["support_domains"] == 6
    assert result["globals"]["avg_falsification_tests_per_term"] == 3.0
    assert result["paths"]["regime_shift"] is None


def test_compute_truth_map_adds_regime_shift_risk_boost(tmp_path: Path) -> None:
    evidence_metrics = _write_json(
        tmp_path / "evidence.json",
        {"claim_scores": {"claim": {"CSS": 0, "CPR": 0}}},
    )
    proof_integrity = _write_json(tmp_path / "proof.json", {"PIS": 1})
    sig_kpi = _write_json(
        tmp_path / "sig.json",
        {"PDG": {"avg_unique_domains_per_term": 6, "avg_falsification_tests_per_term": 0}},
    )
    regime_shift = _write_json(tmp_path / "regime.json", {"regime_shift": True})
    kwargs = {
        "evidence_metrics_path": evidence_metrics,
        "proof_integrity_path": proof_integrity,
        "sig_kpi_path": sig_kpi,
        "tpl_coord": {
            "tpl_by_claim": {"claim": {"TPL": 1}},
            "coord_by_claim": {"claim": {"COORD": 1}},
        },
    }

    ordinary = truth_contamination.compute_truth_map(**kwargs)
    shifted = truth_contamination.compute_truth_map(**kwargs, regime_shift_path=regime_shift)

    assert ordinary["claims"]["claim"]["ML_score"] == pytest.approx(0.70)
    assert shifted["claims"]["claim"]["ML_score"] == pytest.approx(0.78)
    assert shifted["claims"]["claim"]["inputs"]["regime_shift"] is True


def test_compute_truth_map_handles_non_object_source_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_data = {
        "evidence": {"claim_scores": []},
        "proof": [],
        "sig": {"PDG": []},
        "regime": [],
    }
    monkeypatch.setattr(truth_contamination, "_read_json", lambda path: source_data[path])

    result = truth_contamination.compute_truth_map(
        evidence_metrics_path="evidence",
        proof_integrity_path="proof",
        sig_kpi_path="sig",
        tpl_coord={"tpl_by_claim": [], "coord_by_claim": []},
        regime_shift_path="regime",
    )

    assert result["claims"] == {}
    assert result["quadrant_counts"] == {}
    assert result["globals"] == {
        "PIS": 0.0,
        "avg_unique_domains_per_term": 0.0,
        "avg_falsification_tests_per_term": 0.0,
        "regime_shift": False,
    }


def test_main_uses_latest_reports_and_writes_default_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare_default_cli_tree(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["abx-truth-contamination"])

    assert truth_contamination.main() == 0

    output = capsys.readouterr().out
    assert "[TRUTH_MAP] wrote: out/reports/truth_contamination_" in output
    result_path = next((tmp_path / "out" / "reports").glob("truth_contamination_*.json"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["paths"]["evidence_metrics"] == "out/reports/evidence_metrics_z.json"
    assert result["paths"]["proof_integrity"] == "out/reports/proof_integrity_a.json"
    assert result["paths"]["regime_shift"] == "out/reports/regime_shift_a.json"
    assert result["globals"]["regime_shift"] is True


def test_main_honors_explicit_inputs_window_and_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    input_dir = tmp_path / "inputs"
    evidence = _write_json(input_dir / "evidence.json", {"claim_scores": {}})
    proof = _write_json(input_dir / "proof.json", {"PIS": 0.9})
    sig = _write_json(input_dir / "sig.json", {"PDG": {}})
    regime = _write_json(input_dir / "regime.json", {"regime_shift": False})
    evidence_ledger = _write_jsonl(input_dir / "evidence.jsonl", [])
    anchor_ledger = _write_jsonl(input_dir / "anchors.jsonl", [])
    output_path = "out/custom/truth-map.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "abx-truth-contamination",
            "--evidence-metrics",
            evidence,
            "--proof-integrity",
            proof,
            "--sig-kpi",
            sig,
            "--regime-shift",
            regime,
            "--evidence-graph-ledger",
            evidence_ledger,
            "--anchor-ledger",
            anchor_ledger,
            "--window-runs",
            "3",
            "--out",
            output_path,
        ],
    )

    assert truth_contamination.main() == 0

    assert f"[TRUTH_MAP] wrote: {output_path}" in capsys.readouterr().out
    result = json.loads((tmp_path / output_path).read_text(encoding="utf-8"))
    assert result["paths"] == {
        "evidence_metrics": evidence,
        "proof_integrity": proof,
        "sig_kpi": sig,
        "regime_shift": regime,
    }


def test_module_entrypoint_exits_with_main_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare_default_cli_tree(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["abx-truth-contamination"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(Path(truth_contamination.__file__)), run_name="__main__")

    assert exc_info.value.code == 0
    assert "[TRUTH_MAP] wrote: out/reports/truth_contamination_" in capsys.readouterr().out
