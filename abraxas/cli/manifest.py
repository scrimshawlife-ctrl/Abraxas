"""CLI commands for manifest-first acquisition."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from abraxas.core.canonical import canonical_json, sha256_hex
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.manifest_layer import (
    bulk_execute,
    bulk_plan,
    manifest_discover,
    manifest_only_enforce,
    plan_finite_enforce,
)


@dataclass(frozen=True)
class ManifestRunContext:
    run_id: str
    now_utc: str
    git_hash: str = "unknown"
    subsystem_id: str = "acquisition"

    def rune_ctx(self) -> RuneInvocationContext:
        return RuneInvocationContext(run_id=self.run_id, subsystem_id=self.subsystem_id, git_hash=self.git_hash)


def _build_run_ctx(source_id: str, now_override: Optional[str]) -> ManifestRunContext:
    now = now_override or _utc_now()
    run_id = f"manifest_{source_id}_{sha256_hex(now)[:8]}"
    return ManifestRunContext(run_id=run_id, now_utc=now)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_manifest_discovery(source_id: str, out_path: str, seeds: list[str] | None, now: str | None) -> int:
    run_ctx = _build_run_ctx(source_id, now)
    outputs = manifest_discover(
        source_id,
        seeds=seeds or [],
        window=None,
        run_ctx={"run_id": run_ctx.run_id, "now_utc": run_ctx.now_utc},
        ctx=run_ctx.rune_ctx(),
    )
    _write_json(Path(out_path), outputs)
    return 0


def run_bulk_plan(
    source_id: str,
    manifest_path: str,
    out_path: str,
    start: Optional[str],
    end: Optional[str],
    now: Optional[str],
) -> int:
    run_ctx = _build_run_ctx(source_id, now)
    manifest_artifact = _load_manifest_artifact(Path(manifest_path))
    outputs = bulk_plan(
        manifest_artifact=manifest_artifact,
        window={"start": start, "end": end},
        run_ctx={"run_id": run_ctx.run_id, "now_utc": run_ctx.now_utc},
        ctx=run_ctx.rune_ctx(),
    )
    plan = outputs.get("bulk_plan") or {}
    plan_finite_enforce(steps=plan.get("steps") or [], ctx=run_ctx.rune_ctx())
    _write_json(Path(out_path), outputs)
    return 0


def run_execute_plan(plan_path: str, offline: bool, out_path: Optional[str], now: Optional[str]) -> int:
    plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    plan_payload = plan.get("bulk_plan") or plan
    source_id = plan_payload.get("source_id", "unknown")
    run_ctx = _build_run_ctx(source_id, now)
    manifest_only_enforce(stage="bulk_execute", decodo_used=False, ctx=run_ctx.rune_ctx())
    outputs = bulk_execute(
        bulk_plan=plan_payload,
        offline=offline,
        run_ctx={"run_id": run_ctx.run_id, "now_utc": run_ctx.now_utc},
        ctx=run_ctx.rune_ctx(),
    )
    if out_path:
        _write_json(Path(out_path), outputs)
    return 0


def _load_manifest_artifact(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "manifest_artifact" in payload:
        return payload["manifest_artifact"]
    return payload


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload), encoding="utf-8")
