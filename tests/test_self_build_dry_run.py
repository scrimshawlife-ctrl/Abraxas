from __future__ import annotations

from abraxas.registry.self_build_dry_run import run_self_build_dry_run


def test_dry_run() -> None:
    result = run_self_build_dry_run()
    assert result["schema_version"] == "SelfBuildDryRun.v1"
    assert result["safe_to_simulate"] is True
