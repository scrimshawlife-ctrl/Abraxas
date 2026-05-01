from pathlib import Path

from abraxas.viz.frontend_harness_manifest import build_manifest


def test_manifest_determinism() -> None:
    root = Path("frontend/aal-viz")
    m1 = build_manifest(root)
    m2 = build_manifest(root)
    assert m1 == m2
    assert m1["manifest_id"] == m2["manifest_id"]



def test_lockfile_and_ci_script_present() -> None:
    import json
    root = Path("frontend/aal-viz")
    pkg = json.loads((root / "package.json").read_text(encoding="utf-8"))
    assert (root / "package-lock.json").exists()
    assert pkg["scripts"]["test"] == "vitest run"
    assert pkg["scripts"]["ci:test"] == "npm ci && vitest run"
    m = build_manifest(root)
    assert "package-lock.json" in m["files"]
