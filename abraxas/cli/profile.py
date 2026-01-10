"""CLI for deterministic hardware profiling."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from abraxas.core.canonical import canonical_json
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.profile_layer import profile_export, profile_ingest, profile_run


@dataclass(frozen=True)
class ProfileRunContext:
    run_id: str
    now_utc: str
    git_hash: str = "unknown"
    subsystem_id: str = "profile"

    def rune_ctx(self) -> RuneInvocationContext:
        return RuneInvocationContext(run_id=self.run_id, subsystem_id=self.subsystem_id, git_hash=self.git_hash)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_profile_command(
    *,
    suite: str,
    windows: int,
    repetitions: int,
    warmup: int,
    offline: bool,
    now: str | None,
    out_path: str,
    pin_clocks: bool,
) -> int:
    run_ctx = ProfileRunContext(run_id=f"profile_{suite}", now_utc=now or _utc_now())
    config = {
        "windows": windows,
        "repetitions": repetitions,
        "warmup_runs": warmup,
        "now_utc": run_ctx.now_utc,
        "offline": offline,
        "pin_clocks": pin_clocks,
    }
    outputs = profile_run(config=config, run_ctx=run_ctx.__dict__, ctx=run_ctx.rune_ctx())
    export = profile_export(
        profile_pack=outputs["profile_pack"],
        out_path=out_path,
        ctx=run_ctx.rune_ctx(),
    )
    print(canonical_json({"profile": outputs, "export": export}))
    return 0


def run_profile_ingest(profile_path: str) -> int:
    payload = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    run_ctx = ProfileRunContext(run_id="profile_ingest", now_utc=_utc_now())
    outputs = profile_ingest(profile_pack=payload, ctx=run_ctx.rune_ctx())
    print(canonical_json(outputs))
    return 0
