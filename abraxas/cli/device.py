"""CLI for device profile selection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.device_layer import device_fingerprint, device_profile_resolve, portfolio_select
from abraxas.tuning.device_registry import load_device_profiles


@dataclass(frozen=True)
class DeviceRunContext:
    run_id: str
    now_utc: str
    git_hash: str = "unknown"
    subsystem_id: str = "device"

    def rune_ctx(self) -> RuneInvocationContext:
        return RuneInvocationContext(run_id=self.run_id, subsystem_id=self.subsystem_id, git_hash=self.git_hash)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_device_list() -> int:
    profiles = [profile.canonical_payload() for profile in load_device_profiles()]
    print(canonical_json({"profiles": profiles}))
    return 0


def run_device_detect(now: str | None) -> int:
    run_ctx = DeviceRunContext(run_id="device_detect", now_utc=now or _utc_now())
    result = device_fingerprint(run_ctx=run_ctx.__dict__, ctx=run_ctx.rune_ctx())
    print(canonical_json(result))
    return 0


def run_device_select(now: str | None, dry_run: bool) -> int:
    run_ctx = DeviceRunContext(run_id="device_select", now_utc=now or _utc_now())
    result = portfolio_select(run_ctx=run_ctx.__dict__, dry_run=dry_run, ctx=run_ctx.rune_ctx())
    print(canonical_json(result))
    return 0


def run_device_apply(now: str | None) -> int:
    return run_device_select(now, dry_run=False)
