from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---------------------------------------------------------------------------
# Fixture-fallback for Path.read_text: when a test chdir's into a tmp_path
# and calls Path("tests/fixtures/...").read_text(), resolve the path relative
# to the repo root instead of the (temporary) CWD.
# ---------------------------------------------------------------------------
_ORIGINAL_READ_TEXT = Path.read_text


def _read_text_with_repo_fixture_fallback(self: Path, *args, **kwargs):
    if not self.is_absolute() and str(self).startswith("tests/fixtures/") and not self.exists():
        repo_candidate = REPO_ROOT / self
        if repo_candidate.exists():
            return _ORIGINAL_READ_TEXT(repo_candidate, *args, **kwargs)
    return _ORIGINAL_READ_TEXT(self, *args, **kwargs)


Path.read_text = _read_text_with_repo_fixture_fallback


def _reset_global_state() -> None:
    """Return process-global mutable state to its pristine, import-time value.

    The suite is NOT randomly flaky -- two identical runs produce byte-identical
    failure sets -- but it IS collection-order dependent. Two tests failed only
    depending on which tests ran before them, and both passed in isolation:

      * tests/test_baseline_freeze_pass8.py::test_health_scorecard_and_release_prep_are_deterministic
      * tests/evidence/test_evidence_contract.py::test_athanor_adapter_interface

    The cause is state that lives in module-level singletons and leaks between
    tests. Every one of these starts empty at import, so clearing them before each
    test restores the starting conditions the first test would have seen.
    """
    # Module-level provider registry singleton (abraxas/evidence/provider.py:238).
    # Tests register providers into it, and the registration survives the test.
    try:
        import abraxas.evidence.provider as provider_module

        registry = getattr(provider_module, "provider_registry", None)
        providers = getattr(registry, "_providers", None)
        if isinstance(providers, dict):
            providers.clear()
    except Exception:  # never let isolation itself break a test run
        pass

    # VBM registry score cache (abraxas/casebooks/vbm/registry.py).
    try:
        from abraxas.casebooks.vbm.registry import get_vbm_registry

        cache = getattr(get_vbm_registry(), "_score_cache", None)
        if isinstance(cache, dict):
            cache.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _isolate_global_state():
    """Give every test the same pristine globals regardless of collection order."""
    _reset_global_state()
    yield
