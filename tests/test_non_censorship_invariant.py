from __future__ import annotations

import subprocess
import sys

import pytest

from abraxas.core.provenance import ProvenanceBundle
from abraxas.core.rendering import render_output
from abraxas.drift.orchestrator import analyze_text_for_drift
from abraxas.policy.non_censorship import NonCensorshipViolation, assert_output_unchanged


GOLDEN_SNIPPETS = [
    (
        "Retronic time inversion hums under the Numogram lattice, clock-hands folding "
        "through zero while we chart the inversion and refuse any sanitizing gloss."
    ),
    (
        "I speak with prophetic authority: the edict is already carved, and no mediator "
        "is permitted to rewrite or soften it before it reaches the listener."
    ),
    (
        "The ritual grid frames itself as a totalizing conspiracy of symbols, "
        "naming every witness and forbidding any block on the litany as it rolls forward."
    ),
    (
        "High mythic cadence: the cantor threads neon-seared verses without filtration, "
        "letting every cadence land intact upon the waiting field."
    ),
]


@pytest.mark.parametrize("draft_text", GOLDEN_SNIPPETS)
def test_rendering_is_identity(draft_text: str) -> None:
    rendered = render_output(draft_text, context={"case": "golden_invariant"})
    assert rendered == draft_text


def test_rewrite_raises_violation() -> None:
    with pytest.raises(NonCensorshipViolation):
        assert_output_unchanged(
            "Numogram arc persists.\n",
            "Numogram arc persists but was rewritten for caution.",
            {"case": "intentional_rewrite"},
        )


def test_drift_report_is_metadata_only() -> None:
    text = GOLDEN_SNIPPETS[0]
    report = analyze_text_for_drift(text, ProvenanceBundle())
    assert report.text_sha256, "Drift report should include hashed content metadata"
    assert report.provenance is not None
    assert text == GOLDEN_SNIPPETS[0], "Analysis must not modify the underlying text"


def test_static_scan_enforced() -> None:
    result = subprocess.run(
        [sys.executable, "tools/non_censor_scan.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Static scan failed:\\nSTDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
