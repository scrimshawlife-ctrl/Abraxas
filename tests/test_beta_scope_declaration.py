"""Beta 1 scope is a decision, so it is guarded like one.

docs/BETA_READINESS.md declares empirical and economic settlement explicitly out of scope for beta
1. That declaration is only meaningful if it cannot erode silently: a future session could settle an
engine at either level, or delete the paragraph, and nothing would object.

Two assertions, both driven to failure before being trusted:

1. The declaration exists in BETA_READINESS.md.
2. No engine declares an empirical or economic settlement. The pipeline cannot measure either level,
   so any such claim would be unenforceable by construction. When a measurement pipeline is built,
   this test is the thing that must be deliberately changed, which is the point.

This pins documents, which is a brittle thing to do, and it is deliberate here: the repository
already pins its version across pyproject, canon, README and CHANGELOG
(tests/test_version_single_source.py), and a scope decision is the same kind of fact.
"""

from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
BETA_DOC = REPO / "docs" / "BETA_READINESS.md"
ENGINES = REPO / "abraxas" / "engines"


def _engine_sources() -> list[pathlib.Path]:
    if not ENGINES.is_dir():
        return []
    return sorted(p for p in ENGINES.rglob("*.py") if p.is_file())


def test_beta_doc_declares_empirical_and_economic_out_of_scope() -> None:
    text = BETA_DOC.read_text(encoding="utf-8")
    assert "Beta 1 scope declaration" in text, (
        "docs/BETA_READINESS.md no longer carries the beta 1 scope declaration. Restore it, or "
        "update this test if beta 1 has genuinely ended."
    )
    flat = " ".join(text.split())
    assert "OUT OF SCOPE for beta 1" in flat, "the out-of-scope declaration is missing"
    assert "empirical" in flat and "economic" in flat, (
        "the declaration no longer names the settlement levels it excludes"
    )


def test_no_engine_declares_an_unmeasurable_settlement() -> None:
    """A settlement claim with no pipeline behind it is the failure the technical guards exist for."""
    offenders: list[str] = []
    # Broad on purpose. The first version of this pattern required the level to be followed
    # immediately by `=` or `:`, so it never matched `empirical: str = "settled"` and the assertion
    # could not fail. Planted and caught. Now it tolerates an optional quoted key, an optional type
    # annotation, and either assignment operator, case-insensitively.
    for path in _engine_sources():
        source = path.read_text(encoding="utf-8")
        for level in ("empirical", "economic"):
            pattern = (
                rf"['\"]?{level}['\"]?\s*"
                rf"(?::\s*[A-Za-z_][\w\.\[\]| ]*)?"
                rf"\s*[=:]\s*['\"]?settled['\"]?"
            )
            for m in re.finditer(pattern, source, re.IGNORECASE):
                line_no = source[: m.start()].count("\n") + 1
                offenders.append(
                    f"{path.relative_to(REPO)}:{line_no} declares {level} settled "
                    f"({source.splitlines()[line_no - 1].strip()[:60]!r})"
                )

    assert not offenders, (
        "These declare an empirical or economic settlement, but no survey, harness or test can "
        "measure either level, so the claim is unenforceable by construction:\n  "
        + "\n  ".join(offenders)
        + "\nBuild the measurement pipeline and change this test deliberately, or withdraw the claim."
    )
