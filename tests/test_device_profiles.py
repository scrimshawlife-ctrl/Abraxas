from __future__ import annotations

import json
from pathlib import Path

import pytest

from abraxas.policy.utp import PortfolioTuningIR, UBVBudgets
from abraxas.runtime.device_fingerprint import get_device_fingerprint
from abraxas.tuning.device_profile_schema import DeviceMatchCriteria, DeviceProfile, DeviceProfileProvenance, PortfolioRef
from abraxas.tuning.device_resolver import match_profiles, resolve_device_profile
from abraxas.tuning.device_apply import select_and_apply_portfolio
from abraxas.tuning.device_registry import write_device_profiles


def _portfolio_file(path: Path, portfolio: PortfolioTuningIR) -> None:
    payload = {
        "portfolio_id": portfolio.portfolio_id,
        "ubv": {
            "max_requests_per_run": portfolio.ubv.max_requests_per_run,
            "max_bytes_per_run": portfolio.ubv.max_bytes_per_run,
            "batch_window": portfolio.ubv.batch_window,
            "decodo_policy": {
                "max_requests": portfolio.ubv.decodo_policy.max_requests,
                "manifest_only": portfolio.ubv.decodo_policy.manifest_only,
            },
        },
        "pipeline": {
            "concurrency_enabled": portfolio.pipeline.concurrency_enabled,
            "max_workers_fetch": portfolio.pipeline.max_workers_fetch,
            "max_workers_parse": portfolio.pipeline.max_workers_parse,
            "max_inflight_bytes": portfolio.pipeline.max_inflight_bytes,
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_fingerprint_deterministic() -> None:
    fp1 = get_device_fingerprint({"now_utc": "2026-01-01T00:00:00Z"})
    fp2 = get_device_fingerprint({"now_utc": "2026-01-01T00:00:00Z"})
    assert fp1["fingerprint_hash"] == fp2["fingerprint_hash"]


def test_resolver_specificity_priority() -> None:
    profiles = [
        DeviceProfile(
            profile_id="generic",
            label="desktop",
            match_criteria=DeviceMatchCriteria(cpu_arch=["*"], platform=["*"] , storage_class="*"),
            portfolio_ref=PortfolioRef(portfolio_ir_hash="hash1"),
            priority=10,
            provenance=DeviceProfileProvenance(created_at_utc="2026-01-01T00:00:00Z", author="system"),
        ),
        DeviceProfile(
            profile_id="specific",
            label="orin",
            match_criteria=DeviceMatchCriteria(cpu_arch=["arm64"], platform=["jetson-orin-nano"], storage_class="*"),
            portfolio_ref=PortfolioRef(portfolio_ir_hash="hash2"),
            priority=20,
            provenance=DeviceProfileProvenance(created_at_utc="2026-01-01T00:00:00Z", author="system"),
        ),
    ]
    fingerprint = {
        "cpu_arch": "arm64",
        "platform_id": "jetson-orin-nano",
        "mem_total_bytes": 0,
        "storage_class": None,
        "gpu_present": False,
    }
    selected = resolve_device_profile(fingerprint, profiles)
    assert selected.profile_id == "specific"


def test_atomic_pointer_switch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    portfolio = PortfolioTuningIR(portfolio_id="test")
    portfolio_path = tmp_path / "portfolio.json"
    _portfolio_file(portfolio_path, portfolio)
    device_profile = DeviceProfile(
        profile_id="default",
        label="desktop",
        match_criteria=DeviceMatchCriteria(cpu_arch=["*"], platform=["*"] , storage_class="*"),
        portfolio_ref=PortfolioRef(portfolio_ir_hash=portfolio.hash()),
        priority=1,
        provenance=DeviceProfileProvenance(created_at_utc="2026-01-01T00:00:00Z", author="system"),
    )
    registry_path = tmp_path / "device_profiles.json"
    write_device_profiles([device_profile], path=registry_path)

    monkeypatch.setattr("abraxas.tuning.device_registry.DEFAULT_REGISTRY_PATH", registry_path)
    result = select_and_apply_portfolio(
        {"now_utc": "2026-01-01T00:00:00Z"},
        dry_run=False,
        pointer_path=tmp_path / "ACTIVE",
        portfolio_dir=tmp_path,
        ledger_path=tmp_path / "ledger.jsonl",
    )
    assert result["changed"] is True
    assert (tmp_path / "ACTIVE").read_text(encoding="utf-8").strip() == portfolio_path.name
