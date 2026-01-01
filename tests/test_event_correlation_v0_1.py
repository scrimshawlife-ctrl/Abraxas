from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from abraxas.analysis.event_correlation.correlator import correlate, resolve_pointer
from abraxas.core.canonical import canonical_json


FIX_DIR = os.path.join("tests", "fixtures", "event_correlation")
ENV_DIR = os.path.join(FIX_DIR, "envelopes")
EXPECTED = os.path.join(FIX_DIR, "expected", "drift_report_01.json")


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_envelopes() -> List[Dict[str, Any]]:
    files = sorted([p for p in os.listdir(ENV_DIR) if p.endswith(".json")])
    envs: List[Dict[str, Any]] = []
    for fn in files:
        envs.append(_read_json(os.path.join(ENV_DIR, fn)))
    return envs


def test_event_correlation_determinism_and_golden():
    envs = _load_envelopes()
    a = correlate(envs)
    b = correlate(envs)
    assert canonical_json(a) == canonical_json(b)

    expected = _read_json(EXPECTED)
    assert canonical_json(a) == canonical_json(expected)


def test_event_correlation_stable_under_reordering():
    envs = _load_envelopes()
    # Reverse order is a deterministic perturbation
    out_a = correlate(envs)
    out_b = correlate(list(reversed(envs)))
    assert canonical_json(out_a) == canonical_json(out_b)


def test_event_correlation_pointer_integrity_and_bounds():
    envs = _load_envelopes()
    env_by_id = {e["artifact_id"]: e for e in envs}
    report = correlate(envs)

    for cl in report["clusters"]:
        assert 0.0 <= cl["strength_score"] <= 1.0
        assert 0.0 <= cl["confidence"] <= 1.0
        for ref in cl["evidence_refs"]:
            aid = ref["artifact_id"]
            ptr = ref["pointer"]
            assert aid in env_by_id, f"missing artifact_id in fixture corpus: {aid}"
            val = resolve_pointer(env_by_id[aid], ptr)
            assert val is not None, f"pointer did not resolve: {aid} {ptr}"

