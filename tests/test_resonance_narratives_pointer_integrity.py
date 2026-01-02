import json
from pathlib import Path

from abraxas.renderers.resonance_narratives.renderer import _json_pointer_get, render


FIX_DIR = Path("tests/fixtures/resonance_narratives")


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def _assert_pointer_exists(env, pointer: str):
    _json_pointer_get(env, pointer)


def test_all_pointers_resolve():
    env = _load(FIX_DIR / "envelopes" / "envelope_01.json")
    out = render(env)

    for item in out.get("signal_summary", []):
        _assert_pointer_exists(env, item["pointer"])

    for item in out.get("what_changed", []):
        _assert_pointer_exists(env, item["pointer"])

    for item in out.get("motifs", []):
        _assert_pointer_exists(env, item["pointer"])

