from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType

import pytest

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.ers.types import TaskResult
from abraxas.policy.utp import PipelineKnobs, PortfolioTuningIR, UBVBudgets
from abraxas.runtime.artifacts import ArtifactWriter
from abraxas.runtime.concurrency import ConcurrencyConfig
from abraxas.runtime.deterministic_executor import WorkResult, commit_results, execute_parallel
from abraxas.runtime.device_fingerprint import get_device_fingerprint
from abraxas.runtime.perf_ledger import RuntimePerfLedger
from abraxas.runtime.policy_snapshot import (
    ensure_policy_snapshot,
    load_policy_snapshot,
    policy_ref_from_snapshot,
    verify_policy_snapshot,
)
from abraxas.runtime.results_pack import build_results_pack, make_result_ref
from abraxas.runtime.retention import ArtifactPruner
from abraxas.runtime.work_units import WorkUnit


def test_policy_snapshot_round_trip(tmp_path: Path):
    policy_path = tmp_path / "retention.json"
    policy_payload = {"schema": "RetentionPolicy.v0", "enabled": False}
    policy_path.write_text(json.dumps(policy_payload), encoding="utf-8")

    snapshot_path, snapshot_hash = ensure_policy_snapshot(
        artifacts_dir=str(tmp_path),
        run_id="run_001",
        policy_name="retention",
        policy_path=str(policy_path),
    )

    snap = load_policy_snapshot(snapshot_path, artifacts_dir=str(tmp_path))
    assert snap["schema"] == "PolicySnapshot.v0"
    assert snap["present"] is True
    assert snap["policy_obj"] == policy_payload

    verification = verify_policy_snapshot(snapshot_path, snapshot_hash, artifacts_dir=str(tmp_path))
    assert verification["valid"] is True

    pref = policy_ref_from_snapshot("retention", snapshot_path, snapshot_hash)
    assert pref["schema"] == "PolicyRef.v0"
    assert pref["snapshot_sha256"] == snapshot_hash


def test_pipeline_bindings_resolves_with_fake_registry(monkeypatch: pytest.MonkeyPatch):
    oracle_registry = ModuleType("abraxas.oracle.registry")
    shadow_registry = ModuleType("abraxas.detectors.shadow.registry")

    def run_signal(ctx: dict) -> dict:
        return {"signal": ctx.get("signal")}

    def run_compress(ctx: dict) -> dict:
        return {"compress": ctx.get("compress")}

    def run_overlay(ctx: dict) -> dict:
        return {"overlay": ctx.get("overlay")}

    def get_shadow_tasks(_: dict) -> dict:
        return {"shadow_task": lambda ctx: {"shadow": ctx.get("shadow")}}

    oracle_registry.run_signal = run_signal
    oracle_registry.run_compress = run_compress
    oracle_registry.run_overlay = run_overlay
    shadow_registry.get_shadow_tasks = get_shadow_tasks

    oracle_pkg = ModuleType("abraxas.oracle")
    oracle_pkg.registry = oracle_registry
    shadow_pkg = ModuleType("abraxas.detectors.shadow")
    shadow_pkg.registry = shadow_registry
    detectors_pkg = ModuleType("abraxas.detectors")
    detectors_pkg.shadow = shadow_pkg

    monkeypatch.setitem(sys.modules, "abraxas.oracle", oracle_pkg)
    monkeypatch.setitem(sys.modules, "abraxas.oracle.registry", oracle_registry)
    monkeypatch.setitem(sys.modules, "abraxas.detectors", detectors_pkg)
    monkeypatch.setitem(sys.modules, "abraxas.detectors.shadow", shadow_pkg)
    monkeypatch.setitem(sys.modules, "abraxas.detectors.shadow.registry", shadow_registry)

    from abraxas.runtime.pipeline_bindings import resolve_pipeline_bindings

    bindings = resolve_pipeline_bindings()
    assert bindings.run_signal is run_signal
    assert bindings.run_compress is run_compress
    assert bindings.run_overlay is run_overlay
    assert "shadow_task" in bindings.shadow_tasks
    assert bindings.provenance["oracle"]["signal"] == "abraxas.oracle.registry:run_signal"


def test_artifact_writer_manifest_sorted(tmp_path: Path):
    writer = ArtifactWriter(str(tmp_path))
    writer.write_json(
        run_id="run_001",
        tick=1,
        kind="trendpack",
        schema="TrendPack.v0",
        obj={"ok": True},
        rel_path="viz/run_001/000001.trendpack.json",
    )
    writer.write_json(
        run_id="run_001",
        tick=0,
        kind="runindex",
        schema="RunIndex.v0",
        obj={"ok": True},
        rel_path="run_index/run_001/000000.runindex.json",
    )

    manifest_path = tmp_path / "manifests" / "run_001.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = manifest["records"]
    assert [r["tick"] for r in records] == [0, 1]
    assert records[0]["kind"] == "runindex"


def test_retention_prunes_old_ticks(tmp_path: Path):
    writer = ArtifactWriter(str(tmp_path))
    run_id = "run_001"

    for tick in range(3):
        writer.write_json(
            run_id=run_id,
            tick=tick,
            kind="trendpack",
            schema="TrendPack.v0",
            obj={"tick": tick},
            rel_path=f"viz/{run_id}/{tick:06d}.trendpack.json",
        )
        writer.write_json(
            run_id=run_id,
            tick=tick,
            kind="results",
            schema="ResultsPack.v0",
            obj={"tick": tick},
            rel_path=f"results/{run_id}/{tick:06d}.resultspack.json",
        )
        writer.write_json(
            run_id=run_id,
            tick=tick,
            kind="runindex",
            schema="RunIndex.v0",
            obj={"tick": tick},
            rel_path=f"run_index/{run_id}/{tick:06d}.runindex.json",
        )
        writer.write_json(
            run_id=run_id,
            tick=tick,
            kind="viewpack",
            schema="ViewPack.v0",
            obj={"tick": tick},
            rel_path=f"view/{run_id}/{tick:06d}.viewpack.json",
        )

    pruner = ArtifactPruner(str(tmp_path))
    report = pruner.prune_run(
        run_id,
        policy={
            "schema": "RetentionPolicy.v0",
            "enabled": True,
            "keep_last_ticks": 1,
            "max_bytes_per_run": None,
            "protected_roots": ["manifests", "policy"],
            "compact_manifest": True,
        },
    )

    assert report.kept_ticks == [2]
    assert all("000002" not in Path(path).name for path in report.deleted_files)

    manifest_path = tmp_path / "manifests" / f"{run_id}.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert {rec["tick"] for rec in manifest["records"]} == {2}


def test_results_pack_builds_sorted_items():
    results = {
        "b_task": TaskResult(name="b_task", lane="forecast", status="ok"),
        "a_task": TaskResult(name="a_task", lane="forecast", status="ok"),
    }
    pack = build_results_pack(
        run_id="run_001",
        tick=1,
        results=results,
        provenance={"z": 1, "a": 2},
    )

    assert [item["task"] for item in pack["items"]] == ["a_task", "b_task"]
    assert list(pack["provenance"].keys()) == ["a", "z"]

    ref = make_result_ref(results_pack_path="results.json", task_name="a_task")
    assert ref["schema"] == "ResultRef.v0"


def test_concurrency_from_portfolio_caps_workers():
    portfolio = PortfolioTuningIR(
        ubv=UBVBudgets(max_requests_per_run=2),
        pipeline=PipelineKnobs(concurrency_enabled=True, max_workers_fetch=10, max_workers_parse=3),
    )
    cfg = ConcurrencyConfig.from_portfolio(portfolio)
    assert cfg.enabled is True
    assert cfg.max_workers_fetch == 2
    assert cfg.max_workers_parse == 2


def test_deterministic_executor_commit_order():
    results = [
        WorkResult(unit_id="b", key=("b",), output_refs={}, bytes_processed=1, stage="FETCH"),
        WorkResult(unit_id="a", key=("a",), output_refs={}, bytes_processed=1, stage="FETCH"),
    ]
    committed = commit_results(results)
    assert [res.unit_id for res in committed] == ["a", "b"]


def test_deterministic_executor_execute_parallel_serial():
    units = [
        WorkUnit.build(
            stage="FETCH",
            source_id="s1",
            window_utc={"start": "t0", "end": "t1"},
            key=("a",),
            input_refs={},
            input_bytes=10,
        )
    ]

    def handler(unit: WorkUnit) -> WorkResult:
        return WorkResult(
            unit_id=unit.unit_id,
            key=unit.key,
            output_refs={"ok": True},
            bytes_processed=unit.input_bytes,
            stage=unit.stage,
        )

    cfg = ConcurrencyConfig(enabled=False)
    result = execute_parallel(units, config=cfg, stage="FETCH", handler=handler)
    assert result.workers_used == 1
    assert result.results[0].output_refs["ok"] is True


def test_device_fingerprint_hash(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("abraxas.runtime.device_fingerprint._platform_id", lambda: "linux-test")
    monkeypatch.setattr("abraxas.runtime.device_fingerprint._mem_total_bytes", lambda: 1234)
    monkeypatch.setattr("abraxas.runtime.device_fingerprint._storage_class", lambda: "nvme")
    monkeypatch.setattr("abraxas.runtime.device_fingerprint._gpu_present", lambda: False)
    monkeypatch.setattr("platform.machine", lambda: "x86_64")

    fingerprint = get_device_fingerprint(run_ctx={"now_utc": "2025-01-01T00:00:00Z"})
    expected_payload = {
        "cpu_arch": "x86_64",
        "platform_id": "linux-test",
        "mem_total_bytes": 1234,
        "storage_class": "nvme",
        "gpu_present": False,
    }
    expected_hash = sha256_hex(canonical_json(expected_payload))

    assert fingerprint["fingerprint_hash"] == expected_hash
    assert fingerprint["now_utc"] == "2025-01-01T00:00:00Z"


def test_perf_ledger_records_canonical_json(tmp_path: Path):
    ledger_path = tmp_path / "runtime_parallel.jsonl"
    ledger = RuntimePerfLedger(path=ledger_path)
    payload = {"b": 2, "a": 1}
    ledger.record(payload)

    lines = ledger_path.read_text(encoding="utf-8").splitlines()
    assert lines == [canonical_json(payload)]
