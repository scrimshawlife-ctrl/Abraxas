from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_artifacts import validate_run


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _seed_artifacts(tmp_path: Path) -> dict:
    run_id = "seal"
    tick = 0

    trendpack_path = tmp_path / "viz" / run_id / f"{tick:06d}.trendpack.json"
    resultspack_path = tmp_path / "results" / run_id / f"{tick:06d}.resultspack.json"
    runheader_path = tmp_path / "runs" / f"{run_id}.runheader.json"
    viewpack_path = tmp_path / "view" / run_id / f"{tick:06d}.viewpack.json"
    runindex_path = tmp_path / "run_index" / run_id / f"{tick:06d}.runindex.json"

    _write_json(
        trendpack_path,
        {
            "version": "TrendPack.v0",
            "run_id": run_id,
            "tick": tick,
            "timeline": [
                {
                    "task": "signal",
                    "lane": "core",
                    "status": "ok",
                    "meta": {
                        "result_ref": {
                            "schema": "ResultRef.v0",
                            "results_pack": str(resultspack_path),
                            "task": "signal",
                        }
                    },
                }
            ],
            "provenance": {},
        },
    )
    _write_json(
        resultspack_path,
        {
            "schema": "ResultsPack.v0",
            "run_id": run_id,
            "tick": tick,
            "items": [{"task": "signal", "result": {"ok": True}}],
            "provenance": {},
        },
    )
    _write_json(
        runheader_path,
        {
            "schema": "RunHeader.v0",
            "run_id": run_id,
            "mode": "sandbox",
            "code": {"git_sha": "deadbeef"},
            "pipeline_bindings": {},
            "policy_refs": {},
            "env": {"python": {"version": "3.11", "implementation": "CPython"}},
        },
    )
    _write_json(
        viewpack_path,
        {
            "schema": "ViewPack.v0",
            "run_id": run_id,
            "tick": tick,
            "mode": "sandbox",
            "aggregates": {"stats": {}},
            "events": [],
            "provenance": {},
        },
    )
    _write_json(
        runindex_path,
        {
            "schema": "RunIndex.v0",
            "run_id": run_id,
            "tick": tick,
            "refs": {
                "trendpack": str(trendpack_path),
                "results_pack": str(resultspack_path),
                "run_header": str(runheader_path),
            },
            "hashes": {
                "trendpack_sha256": "a" * 64,
                "results_pack_sha256": "b" * 64,
            },
            "provenance": {"engine": "test", "mode": "sandbox"},
        },
    )

    return {
        "run_id": run_id,
        "tick": tick,
        "trendpack_path": trendpack_path,
        "resultspack_path": resultspack_path,
        "runheader_path": runheader_path,
        "viewpack_path": viewpack_path,
        "runindex_path": runindex_path,
    }


def test_validate_artifacts_pass(tmp_path: Path):
    seed = _seed_artifacts(tmp_path)

    result = validate_run(
        artifacts_dir=str(tmp_path),
        run_id=seed["run_id"],
        tick=seed["tick"],
        schemas_dir=str(Path("schemas")),
    )

    assert result["ok"] is True
    assert result["failures"] == []


def test_validate_artifacts_detects_result_pack_mismatch(tmp_path: Path):
    seed = _seed_artifacts(tmp_path)
    trendpack_path = seed["trendpack_path"]
    trendpack = json.loads(trendpack_path.read_text(encoding="utf-8"))
    trendpack["timeline"][0]["meta"]["result_ref"]["results_pack"] = "wrong.resultspack.json"
    trendpack_path.write_text(json.dumps(trendpack, sort_keys=True), encoding="utf-8")

    result = validate_run(
        artifacts_dir=str(tmp_path),
        run_id=seed["run_id"],
        tick=seed["tick"],
        schemas_dir=str(Path("schemas")),
    )

    assert result["ok"] is False
    assert any(f["artifact_kind"] == "TrendPack.v0" for f in result["failures"])
