import json
from copy import deepcopy
from pathlib import Path

from abraxas.renderers.resonance_narratives.renderer import render


FIX_DIR = Path("tests/fixtures/resonance_narratives")


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def test_overlay_causal_suppression_without_evidence():
    env = _load(FIX_DIR / "envelopes" / "envelope_01.json")
    env2 = deepcopy(env)

    # Force an overlay with causal phrasing
    env2["interpretive_overlay"] = {"summary": "This means that X happened because Y."}

    # Remove any evidence-like fields
    env2.pop("evidence", None)
    env2.pop("evidence_bundle", None)
    env2.pop("evidence_refs", None)

    out = render(env2)
    notes = out.get("overlay_notes", [])
    assert notes, "Expected overlay_notes to exist"
    assert "suppressed" in notes[0]["text"].lower()

