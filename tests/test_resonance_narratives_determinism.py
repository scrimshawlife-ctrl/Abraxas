import json
from pathlib import Path

from abraxas.renderers.resonance_narratives.renderer import render


FIX_DIR = Path("tests/fixtures/resonance_narratives")


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def test_determinism_single_envelope():
    env = _load(FIX_DIR / "envelopes" / "envelope_01.json")
    a = render(env)
    b = render(env)
    assert _canonical(a) == _canonical(b)

