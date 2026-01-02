import json
from pathlib import Path

from abraxas.analysis.event_correlation.correlator import correlate


FIX_DIR = Path("tests/fixtures/event_correlation/envelopes")


def _load_all():
    envs = []
    for p in sorted(FIX_DIR.glob("*.json")):
        envs.append(json.loads(p.read_text(encoding="utf-8")))
    return envs


def test_bounds():
    report = correlate(_load_all())
    for c in report.get("clusters", []):
        assert 0.0 <= float(c["strength_score"]) <= 1.0
        assert 0.0 <= float(c["confidence"]) <= 1.0

