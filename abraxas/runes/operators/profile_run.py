"""ABX-PROFILE_RUN rune operator."""

from __future__ import annotations

from typing import Any, Dict

from abraxas.profile.run import ProfileConfig, run_profile_suite
from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.operators.offline_enforce import apply_offline_enforce
from abraxas.runes.operators.invariance_check import apply_invariance_check


def apply_profile_run(
    *,
    config: Dict[str, Any],
    run_ctx: Dict[str, Any],
    strict_execution: bool = True,
) -> Dict[str, Any]:
    profile_config = ProfileConfig(**config)
    apply_offline_enforce(offline=profile_config.offline)
    ctx = RuneInvocationContext(**run_ctx)
    pack, hash_map = run_profile_suite(profile_config, run_id=run_ctx.get("run_id", "profile"), ctx=ctx)
    for hashes in hash_map.values():
        apply_invariance_check(hashes=hashes)
    return {"profile_pack": pack.model_dump(), "profile_hash": pack.profile_hash()}
