import json
from pathlib import Path

from abraxas.analysis.event_correlation.correlator import correlate


FIX_DIR = Path("tests/fixtures/event_correlation/envelopes")


def _load_all():
    envs = []
    for p in sorted(FIX_DIR.glob("*.json")):
        envs.append(json.loads(p.read_text(encoding="utf-8")))
    return envs


def test_determinism():
    envs = _load_all()
    a = correlate(envs)
    b = correlate(envs)
    assert a["_canonical"] == b["_canonical"]

