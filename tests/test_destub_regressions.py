from pathlib import Path


CRITICAL_FILES = [
    Path("abx/bus/runtime.py"),
    Path("abraxas/aal/neon_genie_adapter.py"),
    Path("abraxas/kernel/dispatcher.py"),
    Path("abraxas/runes/operators/acquisition_layer.py"),
    Path("server/abraxas/upgrade_spine/adapters/shadow_adapter.py"),
    Path("server/abraxas/upgrade_spine/adapters/rent_adapter.py"),
    Path("server/abraxas/upgrade_spine/adapters/drift_adapter.py"),
    Path("server/abraxas/upgrade_spine/adapters/evogate_adapter.py"),
]

FORBIDDEN_PATTERNS = [
    "/stub/",
    "stub mode",
    "patch_plan_stub(",
]


def test_critical_paths_do_not_reintroduce_stub_markers():
    for path in CRITICAL_FILES:
        text = path.read_text(encoding="utf-8").lower()
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in text, f"{pattern!r} reintroduced in {path}"
