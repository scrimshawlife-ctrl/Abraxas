from pathlib import Path

from scripts.familiar.run_v11_prefix import main


def test_v11_prefix_cli_writes_bound_shadow(tmp_path: Path):
    pack = Path("fixtures/familiar/pack_companion_dryrun_2026-09-15.v0.json")
    out = tmp_path / "prefix.json"
    code = main(["--pack", str(pack), "--run-id", "cli_test", "--out", str(out)])
    assert code == 0
    text = out.read_text(encoding="utf-8")
    assert "BOUND_SHADOW" in text
    assert "keep_output.v1" in text
