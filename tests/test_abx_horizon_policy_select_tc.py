from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.horizon_policy_select_tc as policy


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _thresholds() -> dict[str, dict[str, float]]:
    return {
        "wide": {"weeks": 1.0, "months": 1.0, "years": 1.0},
        "tight": {"weeks": 0.0, "months": 0.0, "years": 0.0},
    }


def _install_capability_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    horizon_buckets = {"day": "days", "week": "weeks", "month": "months", "year": "years"}
    classes = {
        "stableterm": "stable",
        "emergingterm": "emerging",
        "volatileterm": "volatile",
        "contestedterm": "contested",
    }

    def invoke(
        operation: str, payload: dict[str, Any], *, ctx: Any, strict_execution: bool
    ) -> dict[str, Any]:
        assert ctx is not None
        assert strict_execution is True
        if operation == "RUNE.FORECAST.TERM_CLASS_MAP.LOAD":
            return {"term_class_map": classes}
        if operation == "forecast.horizon.bucket":
            return {"bucket": horizon_buckets[payload["horizon"]]}
        if operation == "RUNE.FORECAST.SCORING.BRIER":
            probs = payload["probs"]
            outcomes = payload["outcomes"]
            score = sum((p - y) ** 2 for p, y in zip(probs, outcomes, strict=True)) / len(probs)
            return {"brier_score": score}
        if operation == "RUNE.FORECAST.POLICY.CANDIDATES_V0_1":
            return {"policy_candidates": _thresholds()}
        raise AssertionError(f"Unexpected capability: {operation}")

    monkeypatch.setattr(policy, "invoke_capability", invoke)


def test_utc_timestamp_is_utc_and_has_second_precision() -> None:
    timestamp = policy._utc_now_iso()

    assert timestamp.endswith("+00:00")
    assert "." not in timestamp


def test_read_jsonl_handles_missing_invalid_non_object_blank_and_limit(tmp_path: Path) -> None:
    assert policy._read_jsonl(str(tmp_path / "missing.jsonl")) == []

    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text('{"first": 1}\n\nnot-json\n[]\n{"last": 2}\n', encoding="utf-8")

    assert policy._read_jsonl(str(ledger)) == [{"first": 1}, {"last": 2}]
    assert policy._read_jsonl(str(ledger), max_lines=2) == [{"first": 1}]
    assert policy._read_jsonl(str(ledger), max_lines=0) == []


@pytest.mark.parametrize(
    ("prediction", "expected"),
    [
        ({"context": {"dmx": {"bucket": " low "}}}, "LOW"),
        ({"context": {"dmx": {"bucket": "med"}}}, "MED"),
        ({"context": {"dmx": {"bucket": "HIGH"}}}, "HIGH"),
        ({"context": {"dmx": {"bucket": "critical"}}}, "UNKNOWN"),
        ({"context": []}, "UNKNOWN"),
        ({}, "UNKNOWN"),
    ],
)
def test_dmx_bucket_normalizes_only_supported_values(
    prediction: dict[str, Any], expected: str
) -> None:
    assert policy._dmx_bucket(prediction) == expected


@pytest.mark.parametrize(
    ("prediction", "expected"),
    [
        ({"term": "  Storm Surge "}, "storm surge"),
        ({"term": "", "terms": [" First Term ", "second"]}, "first term"),
        ({"terms": []}, ""),
        ({"terms": "not-a-list"}, ""),
    ],
)
def test_term_key_prefers_term_then_first_term(prediction: dict[str, Any], expected: str) -> None:
    assert policy._term_key(prediction) == expected


def test_rolling_stats_groups_rows_by_bucket_class_and_horizon(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_capability_fake(monkeypatch)
    rows = [
        {"dmx": "LOW", "class": "stable", "h": "weeks", "p": 0.2, "y": 1},
        {"dmx": "LOW", "class": "stable", "h": "weeks", "p": 0.8, "y": 1},
        {"dmx": "HIGH", "class": "volatile", "h": "years", "p": 0.25, "y": 0},
    ]

    stats = policy._rolling_stats(rows)

    assert stats["LOW"]["stable"]["weeks"] == {"n": 2, "brier": pytest.approx(0.34)}
    assert stats["HIGH"]["volatile"]["years"] == {
        "n": 1,
        "brier": pytest.approx(0.0625),
    }


def test_rolling_stats_uses_nan_when_capability_omits_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(policy, "invoke_capability", lambda *args, **kwargs: {})

    stats = policy._rolling_stats(
        [{"dmx": "LOW", "class": "unknown", "h": "weeks", "p": 0.2, "y": 1}]
    )

    assert stats["LOW"]["unknown"]["weeks"]["n"] == 1
    assert math.isnan(stats["LOW"]["unknown"]["weeks"]["brier"])


def test_main_empty_ledgers_emits_complete_default_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_capability_fake(monkeypatch)
    pred_path = tmp_path / "predictions.jsonl"
    outcome_path = tmp_path / "outcomes.jsonl"
    _write_jsonl(pred_path, [])
    _write_jsonl(outcome_path, [])
    reports = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "horizon_policy_select_tc",
            "--run-id",
            "empty-run",
            "--pred-ledger",
            str(pred_path),
            "--out-ledger",
            str(outcome_path),
            "--out-reports",
            str(reports),
        ],
    )

    assert policy.main() == 0

    output_path = reports / "horizon_policy_selected_tc_empty-run.json"
    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["version"] == "horizon_policy_selected_tc.v0.1"
    assert result["provenance"]["a2_phase"] == str(reports / "a2_phase_empty-run.json")
    assert set(result["selected_by_bucket_and_class"]) == {"LOW", "MED", "HIGH", "UNKNOWN"}
    for bucket in result["selected_by_bucket_and_class"].values():
        assert set(bucket) == {"stable", "emerging", "volatile", "contested", "unknown"}
        assert bucket["unknown"]["selected"] == "wide"
        assert bucket["unknown"]["max_horizon"] == "days"
        assert bucket["unknown"]["final_score"] == 1.0
        assert "INSUFFICIENT_N_WEEKS(n=0)" in bucket["unknown"]["flags"]
    assert "[HORIZON_POLICY_SELECT_TC] wrote:" in capsys.readouterr().out


def test_main_classifies_predictions_selects_horizons_and_clamps_foggy_high_buckets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_capability_fake(monkeypatch)
    predictions = [
        {
            "pred_id": "stable-week",
            "term": "stableterm",
            "p": 0.5,
            "horizon": "week",
            "context": {"dmx": {"bucket": "low"}},
        },
        {
            "pred_id": "stable-month",
            "term": "stableterm",
            "p": 0.5,
            "horizon": "month",
            "context": {"dmx": {"bucket": "low"}},
        },
        {
            "pred_id": "stable-year",
            "term": "stableterm",
            "p": 0.5,
            "horizon": "year",
            "context": {"dmx": {"bucket": "low"}},
        },
        {
            "pred_id": "volatile-week",
            "term": "volatileterm",
            "p": 0.5,
            "horizon": "week",
            "context": {"dmx": {"bucket": "high"}},
        },
        {
            "pred_id": "volatile-month",
            "term": "volatileterm",
            "p": 0.5,
            "horizon": "month",
            "context": {"dmx": {"bucket": "high"}},
        },
        {
            "pred_id": "volatile-year",
            "term": "volatileterm",
            "p": 0.5,
            "horizon": "year",
            "context": {"dmx": {"bucket": "high"}},
        },
        {
            "pred_id": "contested-year",
            "term": "contestedterm",
            "p": 0.5,
            "horizon": "year",
            "context": {"dmx": {"bucket": "high"}},
        },
        {
            "pred_id": "emerging-day",
            "terms": ["emergingterm"],
            "p": 0.0,
            "horizon": "day",
            "context": {"dmx": {"bucket": "med"}},
        },
        {"pred_id": "unknown-term", "term": "unmapped", "p": 0.4, "horizon": "day", "context": {}},
        {
            "pred_id": "fallback-list-term",
            "terms": ["stableterm"],
            "p": 0.5,
            "horizon": "week",
            "context": {"dmx": {"bucket": "low"}},
        },
        {
            "pred_id": "missing-outcome",
            "term": "stableterm",
            "p": 0.5,
            "horizon": "day",
            "context": {},
        },
        {"term": "stableterm", "p": 0.5, "horizon": "day", "context": {}},
    ]
    outcomes = [
        {"pred_id": "stable-week", "result": "hit"},
        {"pred_id": "stable-month", "result": "hit"},
        {"pred_id": "stable-year", "result": "hit"},
        {"pred_id": "volatile-week", "result": "hit"},
        {"pred_id": "volatile-month", "result": "hit"},
        {"pred_id": "volatile-year", "result": "hit"},
        {"pred_id": "contested-year", "result": "miss"},
        {"pred_id": "emerging-day", "result": "miss"},
        {"pred_id": "unknown-term", "result": "miss"},
        {"pred_id": "fallback-list-term", "result": "hit"},
    ]
    pred_path = tmp_path / "predictions.jsonl"
    outcome_path = tmp_path / "outcomes.jsonl"
    _write_jsonl(pred_path, predictions)
    _write_jsonl(outcome_path, outcomes)
    reports = tmp_path / "reports"
    a2_path = tmp_path / "custom-a2.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "horizon_policy_select_tc",
            "--run-id",
            "matrix-run",
            "--pred-ledger",
            str(pred_path),
            "--out-ledger",
            str(outcome_path),
            "--out-reports",
            str(reports),
            "--a2-phase",
            str(a2_path),
            "--window-resolved",
            "100",
            "--min-n",
            "1",
        ],
    )

    assert policy.main() == 0

    result = json.loads(
        (reports / "horizon_policy_selected_tc_matrix-run.json").read_text(encoding="utf-8")
    )
    selected = result["selected_by_bucket_and_class"]
    assert result["provenance"]["a2_phase"] == str(a2_path)
    assert selected["LOW"]["stable"]["selected"] == "wide"
    assert selected["LOW"]["stable"]["max_horizon"] == "years"
    assert selected["LOW"]["stable"]["thresholds"] == _thresholds()["wide"]
    assert selected["HIGH"]["volatile"]["max_horizon"] == "months"
    assert (
        "HIGH_FOG_CLAMP_NO_YEARS_FOR_VOLATILE_OR_CONTESTED" in selected["HIGH"]["volatile"]["flags"]
    )
    assert selected["HIGH"]["contested"]["max_horizon"] == "days"
    assert (
        "HIGH_FOG_CLAMP_NO_YEARS_FOR_VOLATILE_OR_CONTESTED"
        in selected["HIGH"]["contested"]["flags"]
    )
    assert selected["MED"]["emerging"]["max_horizon"] == "days"
    assert selected["UNKNOWN"]["unknown"]["max_horizon"] == "days"
