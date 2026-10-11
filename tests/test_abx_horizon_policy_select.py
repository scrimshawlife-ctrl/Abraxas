from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import pytest

import abx.horizon_policy_select as policy


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _candidate_thresholds() -> dict[str, dict[str, float]]:
    return {
        "permissive": {"weeks": 1.0, "months": 1.0, "years": 1.0},
        "strict": {"weeks": 0.0, "months": 0.0, "years": 0.0},
    }


def _install_capability_fake(monkeypatch: pytest.MonkeyPatch) -> None:
    horizon_buckets = {"day": "days", "week": "weeks", "month": "months", "year": "years"}

    def invoke(
        operation: str, payload: dict[str, Any], *, ctx: Any, strict_execution: bool
    ) -> dict[str, Any]:
        assert ctx is not None
        assert strict_execution is True
        if operation == "forecast.horizon.bucket":
            return {"bucket": horizon_buckets[payload["horizon"]]}
        if operation == "RUNE.FORECAST.SCORING.BRIER":
            probs = payload["probs"]
            outcomes = payload["outcomes"]
            score = sum((p - y) ** 2 for p, y in zip(probs, outcomes, strict=True)) / len(probs)
            return {"brier_score": score}
        if operation == "RUNE.FORECAST.POLICY.CANDIDATES_V0_1":
            return {"policy_candidates": _candidate_thresholds()}
        raise AssertionError(f"Unexpected capability: {operation}")

    monkeypatch.setattr(policy, "invoke_capability", invoke)


def test_utc_timestamp_is_utc_and_has_second_precision() -> None:
    timestamp = policy._utc_now_iso()

    assert timestamp.endswith("+00:00")
    assert "." not in timestamp


def test_read_jsonl_handles_missing_file_blank_invalid_non_object_and_limit(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    assert policy._read_jsonl(str(missing)) == []

    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text('{"first": 1}\n\nnot-json\n[]\n{"last": 2}\n', encoding="utf-8")

    assert policy._read_jsonl(str(ledger)) == [{"first": 1}, {"last": 2}]
    assert policy._read_jsonl(str(ledger), max_lines=2) == [{"first": 1}]
    assert policy._read_jsonl(str(ledger), max_lines=0) == []


@pytest.mark.parametrize(
    ("prediction", "expected"),
    [
        ({"context": {"dmx": {"bucket": " low "}}}, "LOW"),
        ({"context": {"dmx": {"bucket": "MED"}}}, "MED"),
        ({"context": {"dmx": {"bucket": "high"}}}, "HIGH"),
        ({"context": {"dmx": {"bucket": "critical"}}}, "UNKNOWN"),
        ({"context": []}, "UNKNOWN"),
        ({}, "UNKNOWN"),
    ],
)
def test_dmx_bucket_normalizes_only_supported_buckets(
    prediction: dict[str, Any], expected: str
) -> None:
    assert policy._dmx_bucket(prediction) == expected


@pytest.mark.parametrize(
    ("pred_id", "expected"),
    [("forecast_SHADOW", True), ("forecast", False), ("forecast_shadow", False)],
)
def test_shadow_detection_is_suffix_case_sensitive(pred_id: str, expected: bool) -> None:
    assert policy._is_shadow(pred_id) is expected


@pytest.mark.parametrize(
    ("allowed", "expected"),
    [
        ({}, "days"),
        ({"weeks": True}, "weeks"),
        ({"weeks": True, "months": True}, "months"),
        ({"weeks": True, "months": True, "years": True}, "years"),
        ({"weeks": False, "months": True, "years": False}, "months"),
    ],
)
def test_choose_max_horizon_returns_longest_enabled_choice(
    allowed: dict[str, bool], expected: str
) -> None:
    assert policy._choose_max_horizon(allowed) == expected


def test_rolling_stats_groups_rows_and_returns_brier_scores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_capability_fake(monkeypatch)
    rows = [
        {"dmx": "LOW", "h": "weeks", "p": 0.2, "y": 1},
        {"dmx": "LOW", "h": "weeks", "p": 0.8, "y": 1},
        {"dmx": "HIGH", "h": "years", "p": 0.25, "y": 0},
    ]

    stats = policy._rolling_stats(rows)

    assert stats["LOW"]["weeks"] == {"n": 2, "brier": pytest.approx(0.34)}
    assert stats["HIGH"]["years"] == {"n": 1, "brier": pytest.approx(0.0625)}


def test_rolling_stats_uses_nan_when_capability_omits_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(policy, "invoke_capability", lambda *args, **kwargs: {})

    stats = policy._rolling_stats([{"dmx": "LOW", "h": "weeks", "p": 0.2, "y": 1}])

    assert stats["LOW"]["weeks"]["n"] == 1
    assert math.isnan(stats["LOW"]["weeks"]["brier"])


def test_main_empty_ledgers_writes_default_policy_for_each_bucket(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _install_capability_fake(monkeypatch)
    predictions = tmp_path / "empty-predictions.jsonl"
    outcomes = tmp_path / "empty-outcomes.jsonl"
    _write_jsonl(predictions, [])
    _write_jsonl(outcomes, [])
    reports = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "horizon_policy_select",
            "--run-id",
            "empty-run",
            "--pred-ledger",
            str(predictions),
            "--out-ledger",
            str(outcomes),
            "--out-reports",
            str(reports),
        ],
    )

    assert policy.main() == 0

    candidate_path = reports / "horizon_policy_candidates_empty-run.json"
    selected_path = reports / "horizon_policy_selected_empty-run.json"
    candidates = json.loads(candidate_path.read_text(encoding="utf-8"))
    selected = json.loads(selected_path.read_text(encoding="utf-8"))
    assert candidates["version"] == "horizon_policy_candidates.v0.1"
    assert candidates["results"]["by_bucket"]["LOW"]["permissive"]["score"] == 1.0
    assert selected["selected_by_bucket"]["UNKNOWN"]["selected"] == "permissive"
    assert selected["selected_by_bucket"]["UNKNOWN"]["max_horizon"] == "days"
    assert "INSUFFICIENT_N_WEEKS(n=0)" in selected["selected_by_bucket"]["UNKNOWN"]["flags"]
    assert "[HORIZON_POLICY_SELECT] wrote:" in capsys.readouterr().out


def test_main_pairs_shadow_predictions_scores_buckets_and_selects_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_capability_fake(monkeypatch)
    predictions = [
        {"pred_id": "low-a", "p": 0.2, "horizon": "week", "context": {"dmx": {"bucket": "low"}}},
        {
            "pred_id": "low-a_SHADOW",
            "p": 0.9,
            "horizon": "week",
            "context": {"dmx": {"bucket": "low"}},
        },
        {"pred_id": "low-b", "p": 0.1, "horizon": "week", "context": {"dmx": {"bucket": "low"}}},
        {
            "pred_id": "low-b_SHADOW",
            "p": 0.4,
            "horizon": "week",
            "context": {"dmx": {"bucket": "low"}},
        },
        {
            "pred_id": "high-week",
            "p": 0.5,
            "horizon": "week",
            "context": {"dmx": {"bucket": "high"}},
        },
        {
            "pred_id": "high-month",
            "p": 0.5,
            "horizon": "month",
            "context": {"dmx": {"bucket": "high"}},
        },
        {
            "pred_id": "high-year",
            "p": 0.5,
            "horizon": "year",
            "context": {"dmx": {"bucket": "high"}},
        },
        {"pred_id": "med-day", "p": 0.0, "horizon": "day", "context": {"dmx": {"bucket": "med"}}},
        {"pred_id": "unknown-day", "p": 0.5, "horizon": "day", "context": "bad-shape"},
        {"pred_id": "orphan_SHADOW", "p": 0.5, "horizon": "day", "context": {}},
        {"pred_id": "missing-outcome", "p": 0.5, "horizon": "day", "context": {}},
        {"p": 0.5, "horizon": "day", "context": {}},
    ]
    outcomes = [
        {"pred_id": "low-a", "result": "hit"},
        {"pred_id": "low-a_SHADOW", "result": "hit"},
        {"pred_id": "low-b", "result": "miss"},
        {"pred_id": "low-b_SHADOW", "result": "miss"},
        {"pred_id": "high-week", "result": "hit"},
        {"pred_id": "high-month", "result": "miss"},
        {"pred_id": "high-year", "result": "hit"},
        {"pred_id": "med-day", "result": "hit"},
        {"pred_id": "unknown-day", "result": "miss"},
        {"pred_id": "orphan_SHADOW", "result": "hit"},
    ]
    pred_path = tmp_path / "predictions.jsonl"
    outcome_path = tmp_path / "outcomes.jsonl"
    _write_jsonl(pred_path, predictions)
    _write_jsonl(outcome_path, outcomes)
    reports = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "horizon_policy_select",
            "--run-id",
            "integration-run",
            "--pred-ledger",
            str(pred_path),
            "--out-ledger",
            str(outcome_path),
            "--out-reports",
            str(reports),
            "--window-resolved",
            "100",
            "--min-n",
            "1",
        ],
    )

    assert policy.main() == 0

    candidate_data = json.loads(
        (reports / "horizon_policy_candidates_integration-run.json").read_text(encoding="utf-8")
    )
    selected_data = json.loads(
        (reports / "horizon_policy_selected_integration-run.json").read_text(encoding="utf-8")
    )
    low = candidate_data["results"]["by_bucket"]["LOW"]
    high = candidate_data["results"]["by_bucket"]["HIGH"]
    assert low["permissive"]["shadow_better_rate"] == pytest.approx(0.5)
    assert low["permissive"]["max_horizon"] == "weeks"
    assert low["strict"]["max_horizon"] == "days"
    assert any(flag.startswith("BRIER_TOO_HIGH_WEEKS") for flag in low["strict"]["flags"])
    assert "HIGH_BUCKET_CLAMP_NO_YEARS" in high["permissive"]["flags"]
    assert high["permissive"]["max_horizon"] == "months"
    assert (
        candidate_data["results"]["by_bucket"]["MED"]["permissive"]["rolling_stats"]["days"]["n"]
        == 1
    )
    assert (
        candidate_data["results"]["by_bucket"]["UNKNOWN"]["permissive"]["rolling_stats"]["days"][
            "n"
        ]
        == 2
    )
    assert selected_data["selected_by_bucket"]["LOW"]["selected"] == "permissive"
    assert (
        selected_data["selected_by_bucket"]["LOW"]["thresholds"]
        == _candidate_thresholds()["permissive"]
    )
    assert selected_data["provenance"]["builder"] == "abx.horizon_policy_select.v0.1"


def test_main_applies_resolved_window_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_capability_fake(monkeypatch)
    predictions = [
        {"pred_id": "first", "p": 0.1, "horizon": "week", "context": {"dmx": {"bucket": "low"}}},
        {"pred_id": "second", "p": 0.9, "horizon": "week", "context": {"dmx": {"bucket": "low"}}},
    ]
    outcomes = [{"pred_id": "first", "result": "miss"}, {"pred_id": "second", "result": "hit"}]
    pred_path = tmp_path / "predictions.jsonl"
    outcome_path = tmp_path / "outcomes.jsonl"
    _write_jsonl(pred_path, predictions)
    _write_jsonl(outcome_path, outcomes)
    reports = tmp_path / "reports"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "horizon_policy_select",
            "--run-id",
            "window-run",
            "--pred-ledger",
            str(pred_path),
            "--out-ledger",
            str(outcome_path),
            "--out-reports",
            str(reports),
            "--window-resolved",
            "1",
            "--min-n",
            "1",
        ],
    )

    assert policy.main() == 0

    candidates = json.loads(
        (reports / "horizon_policy_candidates_window-run.json").read_text(encoding="utf-8")
    )
    stats = candidates["results"]["by_bucket"]["LOW"]["permissive"]["rolling_stats"]["weeks"]
    assert stats == {"n": 1, "brier": pytest.approx(0.01)}
