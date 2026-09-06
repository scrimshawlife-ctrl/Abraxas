"""Unit tests for TimesFM Shadow Notion projection T1-T2. No Notion calls."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from abraxas.sources.timesfm_shadow_projection import (
    AUTHORITY_BADGE,
    INFLUENCE,
    LANE,
    PROJECTION_SEMANTICS,
    PROJECTION_SOURCE_ID,
    SCHEMA_VERSION,
    _as_float_list,
    _as_int,
    _as_mapping,
    _as_str,
    _fold_in_feeds,
    _mean_summary,
    _optional_int,
    _optional_str,
    _quantiles,
    _relative_path,
    load_projection_schema,
    main,
    project_packet_bytes,
    project_packet_path,
    projection_schema_path,
    validate_projection,
    write_projection,
)

_REPO = Path(__file__).resolve().parents[1]
_MODULE = _REPO / "abraxas" / "sources" / "timesfm_shadow_projection.py"
_GOLDEN_PACKET = (
    _REPO / "tests" / "fixtures" / "timesfm_shadow" / "timesfm_shadow_forecast.v0.golden.json"
)
_GOLDEN_PROJECTION = (
    _REPO
    / "tests"
    / "fixtures"
    / "timesfm_shadow"
    / "timesfm_shadow_notion_projection.v0.golden.json"
)
_FORBIDDEN_HISTORY = ("timestamps", "values", "history")
_FORBIDDEN_IMPORTS = frozenset(
    {
        "urllib",
        "requests",
        "httpx",
        "notion_client",
        "socket",
        "http.client",
        "http.server",
    }
)


def _packet_payload() -> dict:
    return json.loads(_GOLDEN_PACKET.read_text(encoding="utf-8"))


def _write_packet(tmp_path: Path, payload: dict, name: str = "packet.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_golden_round_trip() -> None:
    projected = project_packet_path(_GOLDEN_PACKET, repo_root=_REPO)
    golden = json.loads(_GOLDEN_PROJECTION.read_text(encoding="utf-8"))
    assert projected == golden
    raw = _GOLDEN_PACKET.read_bytes()
    assert projected["packet_hash"] == hashlib.sha256(raw).hexdigest()
    Draft202012Validator(load_projection_schema()).validate(projected)


def test_valid_for_forecast_forced_false_when_input_lies(tmp_path: Path) -> None:
    payload = _packet_payload()
    payload["valid_for_forecast"] = True
    payload["lane"] = "FORECAST"
    payload["influence_policy"] = "DIRECT"
    payload["semantics"] = "objective_probability"
    path = _write_packet(tmp_path, payload)
    projected = project_packet_path(path, repo_root=tmp_path)
    assert projected["valid_for_forecast"] is False
    assert projected["lane"] == LANE
    assert projected["influence"] == INFLUENCE
    assert projected["semantics"] == PROJECTION_SEMANTICS
    assert "objective_probability" not in json.dumps(projected)


def test_history_arrays_absent_and_ids_split() -> None:
    projected = project_packet_path(_GOLDEN_PACKET, repo_root=_REPO)
    dumped = json.dumps(projected)
    for key in _FORBIDDEN_HISTORY:
        assert key not in projected
        assert f'"{key}"' not in dumped
    assert projected["source_id"] == PROJECTION_SOURCE_ID
    assert projected["source_id"] != projected["series_ref"]
    assert projected["series_ref"] == "EXT.ENERGY_CHARTS.PRICE.v1"
    assert projected["hf_model"] == "google/timesfm-2.5-200m-transformers"
    assert projected["authority_badge"] == AUTHORITY_BADGE
    assert projected["schema_version"] == SCHEMA_VERSION
    assert projected["history_len"] == 2
    assert projected["horizon"] == 2
    assert projected["quantiles"]["q10"] == [0.0, 1.0]
    assert projected["quantiles"]["q50"] == [1.0, 2.0]
    assert projected["quantiles"]["q90"] == [2.0, 3.0]
    assert projected["mean_summary"] == {"last": 2.0, "n": 2}
    assert projected["fold_in_feeds"] == [
        {"target": "RUNE.TIMESFM_FORECAST", "authority": "none"},
        {"target": "MONTE_FORECAST", "authority": "none"},
        {"target": "BIAS_DELTA", "authority": "none"},
    ]
    assert projected["local_path"] == (
        "tests/fixtures/timesfm_shadow/timesfm_shadow_forecast.v0.golden.json"
    )


def test_optional_fields_omitted_when_absent(tmp_path: Path) -> None:
    payload = _packet_payload()
    del payload["hf_revision"]
    del payload["license"]
    del payload["seed"]
    del payload["bzn"]
    del payload["forecast"]["mean"]
    del payload["fold_in"]
    path = _write_packet(tmp_path, payload)
    projected = project_packet_path(path, repo_root=tmp_path)
    assert "hf_revision" not in projected
    assert "license" not in projected
    assert "seed" not in projected
    assert "bzn" not in projected
    assert "mean_summary" not in projected
    assert projected["fold_in_feeds"] == []
    assert projected["valid_for_forecast"] is False


def test_fold_in_feeds_empty_when_feeds_missing(tmp_path: Path) -> None:
    payload = _packet_payload()
    payload["fold_in"] = {}
    path = _write_packet(tmp_path, payload)
    projected = project_packet_path(path, repo_root=tmp_path)
    assert projected["fold_in_feeds"] == []


def test_fail_closed_on_bad_input(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    with pytest.raises(ValueError, match="packet file not found"):
        project_packet_path(missing)
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        project_packet_path(tmp_path / "bad.json")
    (tmp_path / "arr.json").write_text("[1]", encoding="utf-8")
    with pytest.raises(ValueError, match="packet must be an object"):
        project_packet_path(tmp_path / "arr.json")
    (tmp_path / "bin.json").write_bytes(b"\xff\xfe")
    with pytest.raises(ValueError, match="not valid JSON"):
        project_packet_path(tmp_path / "bin.json")


def test_fail_closed_on_missing_and_invalid_fields(tmp_path: Path) -> None:
    payload = _packet_payload()
    payload["source_id"] = ""
    with pytest.raises(ValueError, match="source_id"):
        project_packet_path(_write_packet(tmp_path, payload, "empty_source.json"))
    payload = _packet_payload()
    payload["history"]["window_n"] = 0
    with pytest.raises(ValueError, match="history.window_n"):
        project_packet_path(_write_packet(tmp_path, payload, "bad_window.json"))
    payload = _packet_payload()
    payload["forecast"]["horizon"] = 0
    with pytest.raises(ValueError, match="forecast.horizon"):
        project_packet_path(_write_packet(tmp_path, payload, "bad_horizon.json"))
    payload = _packet_payload()
    payload["forecast"]["quantiles"]["q10"] = [0.0]
    with pytest.raises(ValueError, match="q10"):
        project_packet_path(_write_packet(tmp_path, payload, "q10_len.json"))
    payload = _packet_payload()
    payload["fold_in"]["feeds"] = "nope"
    with pytest.raises(ValueError, match="fold_in.feeds"):
        project_packet_path(_write_packet(tmp_path, payload, "feeds.json"))
    payload = _packet_payload()
    payload["fold_in"]["feeds"] = [{"lane": "SHADOW"}]
    with pytest.raises(ValueError, match="target"):
        project_packet_path(_write_packet(tmp_path, payload, "no_target.json"))
    payload = _packet_payload()
    payload["history"] = []
    with pytest.raises(ValueError, match="history must be an object"):
        project_packet_path(_write_packet(tmp_path, payload, "hist.json"))
    payload = _packet_payload()
    payload["hf_revision"] = 1
    with pytest.raises(ValueError, match="hf_revision"):
        project_packet_path(_write_packet(tmp_path, payload, "rev.json"))
    payload = _packet_payload()
    payload["seed"] = True
    with pytest.raises(ValueError, match="seed"):
        project_packet_path(_write_packet(tmp_path, payload, "seed.json"))
    payload = _packet_payload()
    payload["forecast"]["mean"] = ["x"]
    with pytest.raises(ValueError, match="forecast.mean"):
        project_packet_path(_write_packet(tmp_path, payload, "mean.json"))


def test_helpers_fail_closed() -> None:
    with pytest.raises(ValueError, match="label must be an object"):
        _as_mapping([], "label")
    with pytest.raises(ValueError, match="name must be a non-empty string"):
        _as_str("", "name")
    with pytest.raises(ValueError, match="n must be an integer"):
        _as_int(1.5, "n")
    with pytest.raises(ValueError, match="xs must be a non-empty list"):
        _as_float_list([], "xs")
    with pytest.raises(ValueError, match="xs must contain numbers"):
        _as_float_list([True], "xs")
    with pytest.raises(ValueError, match="forecast.quantiles must be an object"):
        _quantiles({"quantiles": []}, 1)
    assert _optional_str({}, "bzn") is None
    assert _optional_int({}, "seed") is None
    assert _mean_summary({}) is None
    assert _fold_in_feeds({}) == []


def test_relative_path_outside_repo(tmp_path: Path) -> None:
    packet = _write_packet(tmp_path, _packet_payload())
    assert _relative_path(packet, _REPO) == packet.as_posix()
    inside = _REPO / "tests" / "fixtures" / "timesfm_shadow" / "timesfm_shadow_forecast.v0.golden.json"
    assert _relative_path(inside, _REPO) == (
        "tests/fixtures/timesfm_shadow/timesfm_shadow_forecast.v0.golden.json"
    )


def test_write_projection_is_idempotent(tmp_path: Path) -> None:
    projected = project_packet_path(_GOLDEN_PACKET, repo_root=_REPO)
    out = tmp_path / "nested" / "projection.json"
    first = write_projection(projected, out)
    second = write_projection(projected, out)
    assert first == second
    assert json.loads(out.read_text(encoding="utf-8")) == projected


def test_validate_and_schema_path() -> None:
    schema = load_projection_schema()
    assert schema["title"] == SCHEMA_VERSION
    assert projection_schema_path().name == "timesfm_shadow_notion_projection.v0.json"
    projected = project_packet_bytes(_GOLDEN_PACKET.read_bytes(), "packet.json")
    validate_projection(projected)
    broken = dict(projected)
    broken["valid_for_forecast"] = True
    with pytest.raises(Exception, match="valid_for_forecast|False"):
        validate_projection(broken)


def test_schema_missing(monkeypatch, tmp_path: Path) -> None:
    missing = tmp_path / "nope.json"
    monkeypatch.setattr(
        "abraxas.sources.timesfm_shadow_projection.projection_schema_path",
        lambda: missing,
    )
    with pytest.raises(ValueError, match="projection schema not found"):
        load_projection_schema()


def test_schema_must_be_object(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "schema.json"
    path.write_text("[1]", encoding="utf-8")
    monkeypatch.setattr(
        "abraxas.sources.timesfm_shadow_projection.projection_schema_path",
        lambda: path,
    )
    with pytest.raises(ValueError, match="projection schema must be an object"):
        load_projection_schema()


def test_cli_writes_and_blocks(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    assert main(["--packet", str(_GOLDEN_PACKET), "--out", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["valid_for_forecast"] is False
    assert payload["source_id"] == PROJECTION_SOURCE_ID
    assert main(["--packet", str(tmp_path / "missing.json"), "--out", str(out)]) == 2
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_cli_module_and_preflight() -> None:
    cp = subprocess.run(
        [
            sys.executable,
            "-m",
            "abraxas.sources.timesfm_shadow_projection",
            "--help",
        ],
        capture_output=True,
        text=True,
        cwd=_REPO,
        env={**os.environ, "PYTHONPATH": "."},
    )
    assert cp.returncode == 0
    assert "timesfm_shadow_notion_projection.v0" in cp.stdout
    ready = subprocess.run(
        [
            sys.executable,
            ".abraxas/scripts/preflight.py",
            "--subsystem",
            "timesfm_shadow_notion_projection_v0",
        ],
        capture_output=True,
        text=True,
        cwd=_REPO,
    )
    assert ready.returncode == 0
    assert "ELIGIBLE" in ready.stdout
    blocked = subprocess.run(
        [
            sys.executable,
            ".abraxas/scripts/preflight.py",
            "--subsystem",
            "timesfm_shadow_notion_projection_v0",
            "--change-class",
            "forecast_active_change",
        ],
        capture_output=True,
        text=True,
        cwd=_REPO,
    )
    assert blocked.returncode == 1
    assert "restricted change class" in blocked.stdout


def test_anti_slop_surface() -> None:
    source = _MODULE.read_text(encoding="utf-8")
    assert len(source.splitlines()) < 500
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
        elif isinstance(node, ast.Name) and node.id == "Any":
            raise AssertionError("Any is forbidden on the shipped projector")
        elif isinstance(node, ast.Attribute) and node.attr == "Any":
            raise AssertionError("typing.Any is forbidden on the shipped projector")
    assert imported.isdisjoint(_FORBIDDEN_IMPORTS)
    assert "notion" not in source.lower() or "Does not write Notion" in source
    assert "FORECAST" not in source or 'LANE = "SHADOW"' in source


def test_golden_packet_is_synthetic_not_live_prices() -> None:
    payload = _packet_payload()
    assert payload["history"]["values"] == [10.0, 11.0]
    assert payload["source_id"] == "EXT.ENERGY_CHARTS.PRICE.v1"
    assert payload["valid_for_forecast"] is False
